from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from ..base import Base


class UserSession(Base):
    __tablename__ = "user_sessions"

    id: Mapped[Uuid] = mapped_column(Uuid, primary_key=True, server_default=func.gen_random_uuid())
    user_id: Mapped[Uuid] = mapped_column(Uuid, index=True, nullable=False)
    session_id: Mapped[Uuid] = mapped_column(Uuid, unique=True, index=True, nullable=False)
    store_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    store_domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.created_at"
    )
    state_snapshots: Mapped[list["AgentStateSnapshot"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", order_by="AgentStateSnapshot.created_at.desc()"
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    __table_args__ = (
        Index("ix_chat_messages_session_id_created_at", "session_id", "created_at"),
    )

    id: Mapped[Uuid] = mapped_column(Uuid, primary_key=True, server_default=func.gen_random_uuid())
    session_id: Mapped[Uuid] = mapped_column(
        ForeignKey("user_sessions.session_id", ondelete="CASCADE"), index=True, nullable=False
    )
    role: Mapped[str] = mapped_column(String(32), nullable=False)  # 'user' or 'assistant'
    content: Mapped[str] = mapped_column(Text, nullable=False)
    products_json: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session: Mapped["UserSession"] = relationship(back_populates="messages")


class AgentStateSnapshot(Base):
    __tablename__ = "agent_state_snapshots"
    __table_args__ = (
        Index("ix_agent_state_snapshots_session_id_created_at", "session_id", "created_at"),
    )

    id: Mapped[Uuid] = mapped_column(Uuid, primary_key=True, server_default=func.gen_random_uuid())
    session_id: Mapped[Uuid] = mapped_column(
        ForeignKey("user_sessions.session_id", ondelete="CASCADE"), index=True, nullable=False
    )
    state_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    session: Mapped["UserSession"] = relationship(back_populates="state_snapshots")
