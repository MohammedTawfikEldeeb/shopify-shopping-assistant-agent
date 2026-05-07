import json
import uuid

import opik
from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from fastapi.responses import StreamingResponse
from loguru import logger
from langchain_core.messages import HumanMessage, AIMessage
import asyncio

from src.agent import ShoppingAgent
from src.agent.agent import _serialize_state
from src.api.schemas.chat import ChatRequest, ChatResponse, CreateSessionRequest, SessionResponse, ChatMessageResponse
from src.api.services.semantic_cache_service import SemanticCacheService
from src.db.repositories.session_repository import UserSessionRepository, ChatMessageRepository, AgentStateSnapshotRepository
from src.api.dependencies import (
    get_user_session_repository,
    get_chat_message_repository,
    get_agent_state_repository,
    get_shopping_agent,
    get_semantic_cache_service,
)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    body: CreateSessionRequest,
    repo: UserSessionRepository = Depends(get_user_session_repository),
) -> SessionResponse:
    existing = await repo.get_by_session_id(body.session_id)
    if existing:
        return SessionResponse.model_validate(existing)
    session = await repo.create_session(
        user_id=body.user_id,
        session_id=body.session_id,
        store_url=body.store_url,
        store_domain=body.store_domain,
    )
    return SessionResponse.model_validate(session)


@router.get("/sessions", response_model=list[SessionResponse])
async def list_sessions(
    user_id: uuid.UUID,
    repo: UserSessionRepository = Depends(get_user_session_repository),
) -> list[SessionResponse]:
    sessions = await repo.list_by_user_id(user_id)
    return [SessionResponse.model_validate(s) for s in sessions]


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageResponse])
async def get_session_messages(
    session_id: uuid.UUID,
    repo: ChatMessageRepository = Depends(get_chat_message_repository),
) -> list[ChatMessageResponse]:
    messages = await repo.list_by_session_id(session_id)
    return [ChatMessageResponse.model_validate(m) for m in messages]


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: uuid.UUID,
    repo: UserSessionRepository = Depends(get_user_session_repository),
):
    deleted = await repo.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"detail": "Session deleted"}


@router.post("", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    background_tasks: BackgroundTasks,
    session_repo: UserSessionRepository = Depends(get_user_session_repository),
    chat_repo: ChatMessageRepository = Depends(get_chat_message_repository),
    state_repo: AgentStateSnapshotRepository = Depends(get_agent_state_repository),
    agent: ShoppingAgent = Depends(get_shopping_agent),
    cache_service: SemanticCacheService | None = Depends(get_semantic_cache_service),
) -> ChatResponse:
    session = await session_repo.get_by_session_id(body.session_id)
    if session is None:
        session = await session_repo.create_session(
            user_id=body.user_id,
            session_id=body.session_id,
            store_domain=body.store_domain,
        )

    latest_snapshot = await state_repo.get_latest_by_session_id(body.session_id)
    has_context = latest_snapshot is not None and latest_snapshot.get("state_json", {}).get("products")

    cached = None
    if cache_service is not None and not has_context:
        try:
            cache_domain = body.store_domain or session.get("store_domain") or "" if session else ""
            cached = await cache_service.lookup(body.message, cache_domain)
        except Exception:
            logger.opt(exception=True).warning("Semantic cache lookup failed, proceeding without cache")

    if cached:
        logger.info("Returning cached response")
        response_text = cached.response
        products = cached.products
        steps = []
        product_sets = [cached.products] if cached.products else []
    else:
        await chat_repo.create_message(
            session_id=body.session_id,
            role="user",
            content=body.message,
        )

        agent_state = None
        if latest_snapshot:
            agent_state = latest_snapshot.get("state_json")

        response_text, products, steps, product_sets, new_state = await agent.chat_with_session(
            user_message=body.message,
            session_state=agent_state,
        )

        await state_repo.save_snapshot(session_id=body.session_id, state_json=new_state)

        await chat_repo.create_message(
            session_id=body.session_id,
            role="assistant",
            content=response_text,
            products_json=products or None,
        )

        if cache_service is not None and not has_context and not products:
            try:
                await cache_service.store(body.message, response_text, products or [], cache_domain)
            except Exception:
                logger.opt(exception=True).warning("Failed to store response in semantic cache")

    background_tasks.add_task(opik.flush_tracker)
    return ChatResponse(response=response_text, products=products or [], steps=steps or [], product_sets=product_sets or [])


@router.post("/stream")
async def chat_stream(
    body: ChatRequest,
    background_tasks: BackgroundTasks,
    session_repo: UserSessionRepository = Depends(get_user_session_repository),
    chat_repo: ChatMessageRepository = Depends(get_chat_message_repository),
    state_repo: AgentStateSnapshotRepository = Depends(get_agent_state_repository),
    agent: ShoppingAgent = Depends(get_shopping_agent),
    cache_service: SemanticCacheService | None = Depends(get_semantic_cache_service),
):
    session = await session_repo.get_by_session_id(body.session_id)
    if session is None:
        session = await session_repo.create_session(
            user_id=body.user_id,
            session_id=body.session_id,
            store_domain=body.store_domain,
        )

    latest_snapshot = await state_repo.get_latest_by_session_id(body.session_id)
    has_context = latest_snapshot is not None and latest_snapshot.get("state_json", {}).get("products")

    cached = None
    cache_domain = body.store_domain or session.get("store_domain") or "" if session else ""
    if cache_service is not None and not has_context:
        try:
            cached = await cache_service.lookup(body.message, cache_domain)
        except Exception:
            logger.opt(exception=True).warning("Semantic cache lookup failed, proceeding without cache")

    async def event_generator():
        if cached:
            logger.info("Returning cached response via stream")
            response_text = cached.response
            products = cached.products or []
            product_sets = [cached.products] if cached.products else []
            steps = []
            
            # Send step
            yield f"data: {json.dumps({'type': 'step', 'step': {'tool': 'cache', 'status': 'done', 'found': len(products)}})}\n\n"
            
            # Stream text
            for chunk in response_text.split(" "):
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk + ' '})}\n\n"
                await asyncio.sleep(0.01)
                
            yield f"data: {json.dumps({'type': 'products', 'products': products, 'product_sets': product_sets, 'steps': steps})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            return

        # Not cached, start agent
        await chat_repo.create_message(
            session_id=body.session_id,
            role="user",
            content=body.message,
        )

        agent_state = None
        if latest_snapshot:
            agent_state = latest_snapshot.get("state_json")

        response_text = ""
        products = []
        steps = []
        product_sets = []
        final_state = None

        try:
            async for event in agent.stream_chat_with_session(
                user_message=body.message,
                session_state=agent_state,
            ):
                event_type = event["event"]
                name = event.get("name", "")
                
                # Yield text chunks
                if event_type == "on_chat_model_stream":
                    tags = event.get("tags", [])
                    # The ChatOpenAI inside summarize_node has 'summarize_llm' tag now
                    if "summarize_llm" in tags:
                        continue
                        
                    chunk = event["data"].get("chunk")
                    if chunk and chunk.content and not getattr(chunk, "tool_calls", None):
                        response_text += chunk.content
                        yield f"data: {json.dumps({'type': 'chunk', 'content': chunk.content})}\n\n"
                
                # Catch state updates
                elif event_type == "on_chain_end":
                    output = event["data"].get("output", {})
                    if isinstance(output, dict):
                        if "steps" in output and output["steps"]:
                            steps = output["steps"]
                            yield f"data: {json.dumps({'type': 'steps_update', 'steps': steps})}\n\n"
                        if "products" in output:
                            products = output["products"]
                        if "product_sets" in output:
                            product_sets = output["product_sets"]
                        
                        # We assume the main graph outputs the full AgentState which has 'messages' and 'summary'
                        if "messages" in output and "summary" in output:
                            final_state = output
        except Exception as e:
            logger.exception("Error during agent stream")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            return
            
        if final_state:
            serialized_state = _serialize_state(final_state)
            await state_repo.save_snapshot(session_id=body.session_id, state_json=serialized_state)
            
            # Find the final text if not fully captured
            if not response_text:
                for msg in reversed(final_state.get("messages", [])):
                    msg_type = getattr(msg, "type", None)
                    if msg_type == "ai" and not getattr(msg, "tool_calls", None):
                        response_text = msg.content
                        break
        
        if not response_text:
            response_text = "Sorry, I couldn't process that."
            
        await chat_repo.create_message(
            session_id=body.session_id,
            role="assistant",
            content=response_text,
            products_json=products or None,
        )

        if cache_service is not None and not has_context and not products:
            try:
                await cache_service.store(body.message, response_text, products or [], cache_domain)
            except Exception:
                logger.opt(exception=True).warning("Failed to store response in semantic cache")

        # Send products and done event
        yield f"data: {json.dumps({'type': 'products', 'products': products, 'product_sets': product_sets, 'steps': steps})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

        # schedule opik flush
        background_tasks.add_task(opik.flush_tracker)

    return StreamingResponse(event_generator(), media_type="text/event-stream")