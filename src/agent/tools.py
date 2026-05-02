import re
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.orm import sessionmaker, selectinload

from src.utils.embedding_service import embed_query
from src.infrastructure.vectordb.providers.pgvector import PGVectorProvider
from src.db.session import get_session
from src.db.models import Product


class ProductRetriever:
    def __init__(self, vector_db: PGVectorProvider, sync_session_factory: sessionmaker):
        self.vector_db = vector_db
        self.collection_name = "product_vectors"
        self.sync_session_factory = sync_session_factory

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

        # Batch lookup all products in a single session with related data eager-loaded
        with get_session(self.sync_session_factory) as session:
            products = session.scalars(
                select(Product)
                .where(Product.shopify_product_id.in_(shopify_ids))
                .options(
                    selectinload(Product.store),
                    selectinload(Product.variants),
                    selectinload(Product.images),
                )
            ).all()

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

        filtered = [p for p in product_list if self._title_matches_query(p.get("title"), query)]
        return filtered if filtered else product_list


class SQLQueryTool:
    def __init__(self, sync_session_factory: sessionmaker):
        self.session_factory = sync_session_factory

    def execute(self, query: str, params: dict | None = None) -> list[dict[str, Any]]:
        cleaned = query.strip()
        if not cleaned.lower().startswith("select"):
            raise ValueError("Only SELECT queries are allowed")
        with get_session(self.session_factory) as session:
            result = session.execute(text(query), params or {})
            return [dict(row) for row in result.mappings().all()]
