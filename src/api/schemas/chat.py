from pydantic import BaseModel, Field
from typing import List
from uuid import UUID
from datetime import datetime


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User message")
    user_id: UUID = Field(..., description="User UUID")
    session_id: UUID = Field(..., description="Session UUID")


class ProductCard(BaseModel):
    id: str
    title: str
    description: str | None = None
    vendor: str | None = None
    product_type: str | None = None
    shopify_product_id: int | None = None
    handle: str | None = None
    link: str | None = None
    image: str | None = None
    price: float | None = None
    available: bool | None = None
    available_sizes: list[str] = []
    available_colors: list[str] = []
    tags: list[str] = []


class ChatResponse(BaseModel):
    response: str
    products: list[ProductCard] = []


class CreateSessionRequest(BaseModel):
    user_id: UUID = Field(..., description="User UUID")
    session_id: UUID = Field(..., description="Session UUID")
    store_url: str | None = Field(default=None, description="Optional store URL")
    store_domain: str | None = Field(default=None, description="Optional store domain")


class SessionResponse(BaseModel):
    id: UUID
    user_id: UUID
    session_id: UUID
    store_url: str | None
    store_domain: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChatMessageResponse(BaseModel):
    id: UUID
    session_id: UUID
    role: str
    content: str
    products_json: list[dict] | None
    created_at: datetime

    class Config:
        from_attributes = True
