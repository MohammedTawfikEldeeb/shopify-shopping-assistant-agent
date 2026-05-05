import asyncio
import json
import re
from typing import Any

from loguru import logger
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import selectinload

from src.utils.embedding_service import embed_query
from src.utils.reranker_service import rerank
from src.infrastructure.vectordb.providers.pgvector import PGVectorProvider
from src.db.session import get_async_session
from src.db.models import Product


class ProductRetriever:
    CANDIDATE_MULTIPLIER = 3

    def __init__(self, vector_db: PGVectorProvider, async_session_factory: async_sessionmaker, *, use_reranker: bool = True):
        self.vector_db = vector_db
        self.collection_name = "product_vectors"
        self.async_session_factory = async_session_factory
        self.use_reranker = use_reranker

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

    def _build_rerank_text(self, product: Product, meta: dict) -> str:
        parts = []
        if product.title:
            parts.append(product.title)
        if product.product_type:
            parts.append(product.product_type)
        if product.vendor:
            parts.append(product.vendor)
        desc = product.description or meta.get("text", "")
        if desc:
            parts.append(desc[:200])
        return " ".join(parts) if parts else product.title or ""

    async def search(self, query: str, top_k: int = 10) -> list[dict[str, Any]]:
        vector = await asyncio.to_thread(embed_query, query)

        candidate_count = top_k * self.CANDIDATE_MULTIPLIER if self.use_reranker else top_k
        results = await self.vector_db.query(self.collection_name, vector, candidate_count)
        if not results:
            return []

        logger.info("Vector search query={} candidates={} top_k={}", query, len(results), top_k)

        shopify_ids = []
        meta_map = {}
        result_texts = {}
        for i, r in enumerate(results):
            meta = r.get("payload", {}).get("metadata", {})
            if not isinstance(meta, dict):
                meta = json.loads(meta) if isinstance(meta, str) else {}
            shopify_id = meta.get("shopify_product_id")
            if shopify_id:
                sid = int(shopify_id)
                shopify_ids.append(sid)
                meta_map[sid] = meta
                result_texts[sid] = r.get("text", "") or meta.get("text", "") or ""

        if not shopify_ids:
            return []

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

            product_map = {}
            for product in products:
                meta = meta_map.get(product.shopify_product_id, {})
                product_map[product.shopify_product_id] = (product, meta)

        if self.use_reranker and len(product_map) > 1:
            rerank_docs = []
            sid_order = []
            for sid, (product, meta) in product_map.items():
                rerank_docs.append(self._build_rerank_text(product, meta))
                sid_order.append(sid)

            ranked_indices = await asyncio.to_thread(rerank, query, rerank_docs, top_k)

            ordered_products = []
            for idx, score in ranked_indices:
                sid = sid_order[idx]
                product, meta = product_map[sid]
                logger.info(
                    "Reranked #{} score={:.4f} title={}",
                    len(ordered_products) + 1,
                    score,
                    product.title,
                )
                ordered_products.append((product, meta, score))
        else:
            ordered_products = [
                (p, m, None) for p, m in product_map.values()
            ]

        product_list = []
        for product, meta, score in ordered_products:
            store_base_url = product.store.base_url if product.store else None
            handle = product.handle or meta.get("handle", "")
            link = f"{store_base_url}/products/{handle}" if store_base_url and handle else None

            price = meta.get("price")
            if (price is None or price == 0) and product.variants:
                prices = [v.price for v in product.variants if v.price is not None]
                if prices:
                    price = float(min(prices))

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