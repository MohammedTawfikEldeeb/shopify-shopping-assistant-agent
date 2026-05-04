import json
import re
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import selectinload

from src.utils.embedding_service import embed_query
from src.infrastructure.vectordb.providers.pgvector import PGVectorProvider
from src.db.session import get_async_session
from src.db.models import Product


class ProductRetriever:
    def __init__(self, vector_db: PGVectorProvider, async_session_factory: async_sessionmaker):
        self.vector_db = vector_db
        self.collection_name = "product_vectors"
        self.async_session_factory = async_session_factory

    @staticmethod
    def _product_matches_query(product: dict, query: str) -> bool:
        title = product.get("title", "")
        product_type = product.get("product_type", "")
        tags = product.get("tags", [])

        query_words = {w.lower() for w in re.findall(r"[a-zA-Z]{3,}", query)}
        if not query_words:
            return True

        title_words = {w.lower() for w in re.findall(r"[a-zA-Z]{3,}", title)}
        type_words = {w.lower() for w in re.findall(r"[a-zA-Z]{3,}", product_type or "")}
        tag_words = set()
        for tag in tags:
            tag_words.update({w.lower() for w in re.findall(r"[a-zA-Z]{3,}", tag)})

        all_words = title_words | type_words | tag_words
        return bool(query_words & all_words)

    async def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        vector = embed_query(query)
        results = await self.vector_db.query(self.collection_name, vector, top_k)
        if not results:
            return []

        # Collect all shopify_ids and metadata from vector DB
        shopify_ids = []
        meta_map = {}
        for r in results:
            meta = r.get("payload", {}).get("metadata", {})
            shopify_id = meta.get("shopify_product_id")
            if shopify_id:
                shopify_ids.append(int(shopify_id))
                meta_map[int(shopify_id)] = meta

        if not shopify_ids:
            return []

        # Batch lookup all products in a single async session with related data eager-loaded
        async with get_async_session(self.async_session_factory) as session:
            result = await session.scalars(
                select(Product)
                .where(Product.shopify_product_id.in_(shopify_ids))
                .options(
                    selectinload(Product.store),
                    selectinload(Product.variants),
                    selectinload(Product.images),
                )
            )
            products = result.all()

            product_list = []
            for product in products:
                meta = meta_map.get(product.shopify_product_id, {})

                # Build product URL
                store_base_url = product.store.base_url if product.store else None
                handle = product.handle or meta.get("handle", "")
                link = f"{store_base_url}/products/{handle}" if store_base_url and handle else None

                # Get price: prefer metadata min price, fallback to SQL variants
                price = meta.get("price")
                if (price is None or price == 0) and product.variants:
                    prices = [v.price for v in product.variants if v.price is not None]
                    if prices:
                        price = float(min(prices))

                # Get image: prefer metadata primary image, fallback to first SQL image
                image = meta.get("primary_image_url")
                if not image and product.images:
                    image = product.images[0].src

                product_list.append({
                    "id": str(product.id),
                    "title": product.title or "",
                    "description": product.description,
                    "vendor": product.vendor or meta.get("vendor"),
                    "product_type": product.product_type or meta.get("product_type"),
                    "shopify_product_id": product.shopify_product_id,
                    "handle": handle,
                    "link": link,
                    "image": image,
                    "price": price,
                    "available": meta.get("available"),
                    "available_sizes": meta.get("available_sizes", []),
                    "available_colors": meta.get("available_colors", []),
                    "tags": meta.get("tags", []),
                })

        filtered = [p for p in product_list if self._product_matches_query(p, query)]
        return filtered if filtered else product_list


class SQLQueryTool:
    def __init__(self, async_session_factory: async_sessionmaker):
        self.async_session_factory = async_session_factory

    async def execute(self, query: str, params: dict | None = None) -> list[dict[str, Any]]:
        cleaned = query.strip()
        if not cleaned.lower().startswith("select"):
            raise ValueError("Only SELECT queries are allowed")
        async with get_async_session(self.async_session_factory) as session:
            result = await session.execute(text(query), params or {})
            return [dict(row) for row in result.mappings().all()]
