import re
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from src.utils.embedding_service import embed_query
from src.infrastructure.vectordb.providers.pgvector import PGVectorProvider
from src.config import get_settings
from src.db.factory import DatabaseFactory, DBType
from src.db.session import get_session
from src.db.models import Product


class ProductRetriever:
    def __init__(self):
        settings = get_settings()
        async_engine = create_async_engine(settings.postgres.async_url)
        async_session_factory = async_sessionmaker(async_engine, class_=AsyncSession)
        self.vector_db = PGVectorProvider(
            db_client=async_session_factory,
            default_vector_size=384,
            distance_method="cosine",
        )
        self.collection_name = "product_vectors"
        self.sync_db = DatabaseFactory.create(DBType.POSTGRES, settings.postgres.url)

    @staticmethod
    def _title_matches_query(title: str | None, query: str) -> bool:
        if not title:
            return False
        # Extract meaningful words (3+ chars) from query
        query_words = {w.lower() for w in re.findall(r"[a-zA-Z]{3,}", query)}
        if not query_words:
            return True
        title_words = {w.lower() for w in re.findall(r"[a-zA-Z]{3,}", title)}
        return bool(query_words & title_words)

    async def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        vector = embed_query(query)
        results = await self.vector_db.query(self.collection_name, vector, top_k)
        products = []
        for r in results:
            meta = r.get("payload", {}).get("metadata", {})
            shopify_id = meta.get("shopify_product_id")
            if not shopify_id:
                continue
            with get_session(self.sync_db.session_factory) as session:
                product = session.scalar(
                    select(Product).where(Product.shopify_product_id == int(shopify_id))
                )
                if product:
                    products.append({
                        "id": str(product.id),
                        "title": product.title,
                        "description": product.description,
                        "vendor": product.vendor,
                        "shopify_product_id": product.shopify_product_id,
                    })

        # Filter: only keep products whose title matches query keywords
        filtered = [p for p in products if self._title_matches_query(p.get("title"), query)]
        # Fallback: if filtering is too aggressive, return original results
        return filtered if filtered else products


class SQLQueryTool:
    def __init__(self):
        settings = get_settings()
        self.db = DatabaseFactory.create(DBType.POSTGRES, settings.postgres.url)

    def execute(self, query: str, params: dict | None = None) -> list[dict[str, Any]]:
        cleaned = query.strip()
        if not cleaned.lower().startswith("select"):
            raise ValueError("Only SELECT queries are allowed")
        with get_session(self.db.session_factory) as session:
            result = session.execute(text(query), params or {})
            return [dict(row) for row in result.mappings().all()]
