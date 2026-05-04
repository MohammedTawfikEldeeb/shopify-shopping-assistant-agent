from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import async_sessionmaker

from ..models.session_models import UserSession, ChatMessage, AgentStateSnapshot
from ..session import get_async_session


def _session_to_dict(obj: UserSession) -> dict[str, Any]:
    return {
        "id": obj.id,
        "user_id": obj.user_id,
        "session_id": obj.session_id,
        "store_url": obj.store_url,
        "store_domain": obj.store_domain,
        "created_at": obj.created_at,
        "updated_at": obj.updated_at,
    }


def _message_to_dict(obj: ChatMessage) -> dict[str, Any]:
    return {
        "id": obj.id,
        "session_id": obj.session_id,
        "role": obj.role,
        "content": obj.content,
        "products_json": obj.products_json,
        "created_at": obj.created_at,
    }


def _snapshot_to_dict(obj: AgentStateSnapshot) -> dict[str, Any]:
    return {
        "id": obj.id,
        "session_id": obj.session_id,
        "state_json": obj.state_json,
        "created_at": obj.created_at,
        "updated_at": obj.updated_at,
    }


class UserSessionRepository:
    def __init__(self, async_session_factory: async_sessionmaker):
        self.async_session_factory = async_session_factory

    async def create_session(
        self,
        user_id: uuid.UUID,
        session_id: uuid.UUID,
        store_url: str | None = None,
        store_domain: str | None = None,
    ) -> dict[str, Any]:
        async with get_async_session(self.async_session_factory) as session:
            obj = UserSession(
                user_id=user_id,
                session_id=session_id,
                store_url=store_url,
                store_domain=store_domain,
            )
            session.add(obj)
            await session.flush()
            await session.refresh(obj)
            return _session_to_dict(obj)

    async def get_by_session_id(self, session_id: uuid.UUID) -> Optional[dict[str, Any]]:
        async with get_async_session(self.async_session_factory) as session:
            obj = await session.scalar(select(UserSession).where(UserSession.session_id == session_id))
            return _session_to_dict(obj) if obj else None

    async def list_by_user_id(self, user_id: uuid.UUID) -> list[dict[str, Any]]:
        async with get_async_session(self.async_session_factory) as session:
            result = await session.scalars(
                select(UserSession)
                .where(UserSession.user_id == user_id)
                .order_by(desc(UserSession.created_at))
            )
            rows = result.all()
            return [_session_to_dict(r) for r in rows]

    async def update_store(
        self,
        session_id: uuid.UUID,
        store_url: str | None,
        store_domain: str | None,
    ) -> Optional[dict[str, Any]]:
        async with get_async_session(self.async_session_factory) as session:
            obj = await session.scalar(select(UserSession).where(UserSession.session_id == session_id))
            if obj is None:
                return None
            if store_url is not None:
                obj.store_url = store_url
            if store_domain is not None:
                obj.store_domain = store_domain
            obj.updated_at = datetime.now().astimezone()
            await session.flush()
            await session.refresh(obj)
            return _session_to_dict(obj)

    async def delete_session(self, session_id: uuid.UUID) -> bool:
        async with get_async_session(self.async_session_factory) as session:
            obj = await session.scalar(select(UserSession).where(UserSession.session_id == session_id))
            if obj is None:
                return False
            await session.delete(obj)
            return True


class ChatMessageRepository:
    def __init__(self, async_session_factory: async_sessionmaker):
        self.async_session_factory = async_session_factory

    async def create_message(
        self,
        session_id: uuid.UUID,
        role: str,
        content: str,
        products_json: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        async with get_async_session(self.async_session_factory) as session:
            obj = ChatMessage(
                session_id=session_id,
                role=role,
                content=content,
                products_json=products_json,
            )
            session.add(obj)
            await session.flush()
            await session.refresh(obj)
            return _message_to_dict(obj)

    async def list_by_session_id(self, session_id: uuid.UUID) -> list[dict[str, Any]]:
        async with get_async_session(self.async_session_factory) as session:
            result = await session.scalars(
                select(ChatMessage)
                .where(ChatMessage.session_id == session_id)
                .order_by(ChatMessage.created_at)
            )
            rows = result.all()
            return [_message_to_dict(r) for r in rows]


class AgentStateSnapshotRepository:
    def __init__(self, async_session_factory: async_sessionmaker):
        self.async_session_factory = async_session_factory

    async def save_snapshot(self, session_id: uuid.UUID, state_json: dict[str, Any]) -> dict[str, Any]:
        async with get_async_session(self.async_session_factory) as session:
            obj = AgentStateSnapshot(session_id=session_id, state_json=state_json)
            session.add(obj)
            await session.flush()
            await session.refresh(obj)
            return _snapshot_to_dict(obj)

    async def get_latest_by_session_id(self, session_id: uuid.UUID) -> Optional[dict[str, Any]]:
        async with get_async_session(self.async_session_factory) as session:
            obj = await session.scalar(
                select(AgentStateSnapshot)
                .where(AgentStateSnapshot.session_id == session_id)
                .order_by(desc(AgentStateSnapshot.created_at))
                .limit(1)
            )
            return _snapshot_to_dict(obj) if obj else None
