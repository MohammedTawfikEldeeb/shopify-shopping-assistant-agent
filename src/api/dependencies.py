from fastapi import Request

from src.agent import ShoppingAgent
from src.api.services.semantic_cache_service import SemanticCacheService
from src.db.repositories.session_repository import (
    AgentStateSnapshotRepository,
    ChatMessageRepository,
    UserSessionRepository,
)


def get_user_session_repository(request: Request) -> UserSessionRepository:
    return request.app.state.user_session_repository


def get_chat_message_repository(request: Request) -> ChatMessageRepository:
    return request.app.state.chat_message_repository


def get_agent_state_repository(request: Request) -> AgentStateSnapshotRepository:
    return request.app.state.agent_state_repository


def get_shopping_agent(request: Request) -> ShoppingAgent:
    return request.app.state.shopping_agent


def get_semantic_cache_service(request: Request) -> SemanticCacheService | None:
    return getattr(request.app.state, "semantic_cache_service", None)