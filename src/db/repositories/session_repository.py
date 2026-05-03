from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import select, desc
from sqlalchemy.orm import sessionmaker

from ..models.session_models import UserSession, ChatMessage, AgentStateSnapshot
from ..session import get_session


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
    def __init__(self, session_factory: sessionmaker):
        self.session_factory = session_factory

    def create_session(
        self,
        user_id: uuid.UUID,
        session_id: uuid.UUID,
        store_url: str | None = None,
        store_domain: str | None = None,
    ) -> dict[str, Any]:
        with get_session(self.session_factory) as session:
            obj = UserSession(
                user_id=user_id,
                session_id=session_id,
                store_url=store_url,
                store_domain=store_domain,
            )
            session.add(obj)
            session.flush()
            session.refresh(obj)
            return _session_to_dict(obj)

    def get_by_session_id(self, session_id: uuid.UUID) -> Optional[dict[str, Any]]:
        with get_session(self.session_factory) as session:
            obj = session.scalar(select(UserSession).where(UserSession.session_id == session_id))
            return _session_to_dict(obj) if obj else None

    def list_by_user_id(self, user_id: uuid.UUID) -> list[dict[str, Any]]:
        with get_session(self.session_factory) as session:
            rows = session.scalars(
                select(UserSession)
                .where(UserSession.user_id == user_id)
                .order_by(desc(UserSession.created_at))
            ).all()
            return [_session_to_dict(r) for r in rows]

    def update_store(
        self,
        session_id: uuid.UUID,
        store_url: str | None,
        store_domain: str | None,
    ) -> Optional[dict[str, Any]]:
        with get_session(self.session_factory) as session:
            obj = session.scalar(select(UserSession).where(UserSession.session_id == session_id))
            if obj is None:
                return None
            if store_url is not None:
                obj.store_url = store_url
            if store_domain is not None:
                obj.store_domain = store_domain
            obj.updated_at = datetime.now().astimezone()
            session.flush()
            session.refresh(obj)
            return _session_to_dict(obj)

    def delete_session(self, session_id: uuid.UUID) -> bool:
        with get_session(self.session_factory) as session:
            obj = session.scalar(select(UserSession).where(UserSession.session_id == session_id))
            if obj is None:
                return False
            session.delete(obj)
            return True


class ChatMessageRepository:
    def __init__(self, session_factory: sessionmaker):
        self.session_factory = session_factory

    def create_message(
        self,
        session_id: uuid.UUID,
        role: str,
        content: str,
        products_json: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        with get_session(self.session_factory) as session:
            obj = ChatMessage(
                session_id=session_id,
                role=role,
                content=content,
                products_json=products_json,
            )
            session.add(obj)
            session.flush()
            session.refresh(obj)
            return _message_to_dict(obj)

    def list_by_session_id(self, session_id: uuid.UUID) -> list[dict[str, Any]]:
        with get_session(self.session_factory) as session:
            rows = session.scalars(
                select(ChatMessage)
                .where(ChatMessage.session_id == session_id)
                .order_by(ChatMessage.created_at)
            ).all()
            return [_message_to_dict(r) for r in rows]


class AgentStateSnapshotRepository:
    def __init__(self, session_factory: sessionmaker):
        self.session_factory = session_factory

    def save_snapshot(self, session_id: uuid.UUID, state_json: dict[str, Any]) -> dict[str, Any]:
        with get_session(self.session_factory) as session:
            obj = AgentStateSnapshot(session_id=session_id, state_json=state_json)
            session.add(obj)
            session.flush()
            session.refresh(obj)
            return _snapshot_to_dict(obj)

    def get_latest_by_session_id(self, session_id: uuid.UUID) -> Optional[dict[str, Any]]:
        with get_session(self.session_factory) as session:
            obj = session.scalar(
                select(AgentStateSnapshot)
                .where(AgentStateSnapshot.session_id == session_id)
                .order_by(desc(AgentStateSnapshot.created_at))
                .limit(1)
            )
            return _snapshot_to_dict(obj) if obj else None
