import json
import uuid

import opik
from fastapi import APIRouter, BackgroundTasks, Request, HTTPException
from langchain_core.messages import HumanMessage, AIMessage

from src.agent import ShoppingAgent
from src.api.schemas.chat import ChatRequest, ChatResponse, CreateSessionRequest, SessionResponse, ChatMessageResponse
from src.db.repositories.session_repository import UserSessionRepository, ChatMessageRepository, AgentStateSnapshotRepository

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/sessions", response_model=SessionResponse)
async def create_session(body: CreateSessionRequest, request: Request) -> SessionResponse:
    repo: UserSessionRepository = request.app.state.user_session_repository
    existing = repo.get_by_session_id(body.session_id)
    if existing:
        return SessionResponse.model_validate(existing)
    session = repo.create_session(
        user_id=body.user_id,
        session_id=body.session_id,
        store_url=body.store_url,
        store_domain=body.store_domain,
    )
    return SessionResponse.model_validate(session)


@router.get("/sessions", response_model=list[SessionResponse])
async def list_sessions(user_id: uuid.UUID, request: Request) -> list[SessionResponse]:
    repo: UserSessionRepository = request.app.state.user_session_repository
    sessions = repo.list_by_user_id(user_id)
    return [SessionResponse.model_validate(s) for s in sessions]


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageResponse])
async def get_session_messages(session_id: uuid.UUID, request: Request) -> list[ChatMessageResponse]:
    repo: ChatMessageRepository = request.app.state.chat_message_repository
    messages = repo.list_by_session_id(session_id)
    return [ChatMessageResponse.model_validate(m) for m in messages]


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: uuid.UUID, request: Request):
    repo: UserSessionRepository = request.app.state.user_session_repository
    deleted = repo.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"detail": "Session deleted"}


@router.post("", response_model=ChatResponse)
async def chat(body: ChatRequest, request: Request, background_tasks: BackgroundTasks) -> ChatResponse:
    # Ensure session exists
    session_repo: UserSessionRepository = request.app.state.user_session_repository
    session = session_repo.get_by_session_id(body.session_id)
    if session is None:
        session = session_repo.create_session(
            user_id=body.user_id,
            session_id=body.session_id,
        )

    chat_repo: ChatMessageRepository = request.app.state.chat_message_repository
    state_repo: AgentStateSnapshotRepository = request.app.state.agent_state_repository

    # Save user message
    chat_repo.create_message(
        session_id=body.session_id,
        role="user",
        content=body.message,
    )

    # Build or load agent state
    latest_snapshot = state_repo.get_latest_by_session_id(body.session_id)
    agent_state = None
    if latest_snapshot:
        agent_state = latest_snapshot.get("state_json")

    agent: ShoppingAgent = request.app.state.shopping_agent
    response_text, products, new_state = await agent.chat_with_session(
        user_message=body.message,
        session_state=agent_state,
    )

    # Save agent state snapshot
    state_repo.save_snapshot(session_id=body.session_id, state_json=new_state)

    # Save assistant message with products
    chat_repo.create_message(
        session_id=body.session_id,
        role="assistant",
        content=response_text,
        products_json=products or None,
    )

    background_tasks.add_task(opik.flush_tracker)
    return ChatResponse(response=response_text, products=products or [])
