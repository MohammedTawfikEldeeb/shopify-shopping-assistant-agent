from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User message")


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
