from pydantic import BaseModel, Field


class IndexStoreRequest(BaseModel):
    store: str = Field(..., min_length=1, description="Store domain or URL")


class IndexStoreResponse(BaseModel):
    store_domain: str
    store_base_url: str
    products_url: str
    total_products_received: int
    products_ingested: int
    products_failed: int
