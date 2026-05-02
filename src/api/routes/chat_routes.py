import opik
from fastapi import APIRouter, BackgroundTasks, Request

from src.agent import ShoppingAgent
from src.api.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(body: ChatRequest, request: Request, background_tasks: BackgroundTasks) -> ChatResponse:
    agent: ShoppingAgent = request.app.state.shopping_agent
    response_text = await agent.chat(body.message)
    products = agent.memory.last_products or []
    background_tasks.add_task(opik.flush_tracker)
    return ChatResponse(response=response_text, products=products)
