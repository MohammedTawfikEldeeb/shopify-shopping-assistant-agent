import asyncio
import json
from typing import Any

import opik
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
    RETRIEVER_TOP_K = 20

    def __init__(self, vector_db: PGVectorProvider, async_session_factory: async_sessionmaker, *, use_reranker: bool = True, min_rerank_score: float = -7.5):
        self.vector_db = vector_db
        self.collection_name = "product_vectors"
        self.async_session_factory = async_session_factory
        self.use_reranker = use_reranker
        self.min_rerank_score = min_rerank_score

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

    @opik.track(name="retriever.search", type="tool", tags=["retriever", "hakeem"])
    async def search(self, query: str, original_query: str | None = None, top_k: int = 30) -> dict[str, Any]:
        steps = []
        steps.append({"tool": "product_retriever", "status": "searching", "query": query, "original_query": original_query})

        rerank_query = original_query if original_query else query
        vector = await asyncio.to_thread(embed_query, query)

        candidate_count = self.RETRIEVER_TOP_K if self.use_reranker else top_k
        results = await self.vector_db.query(self.collection_name, vector, candidate_count)
        if not results:
            steps.append({"tool": "product_retriever", "status": "done", "found": 0})
            return {"products": [], "steps": steps}

        logger.info("Vector search query={} candidates={} top_k={}", query, len(results), top_k)
        steps.append({"tool": "product_retriever", "status": "retrieved", "candidates": len(results)})

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
            steps.append({"tool": "product_retriever", "status": "done", "found": 0})
            return {"products": [], "steps": steps}

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
            steps.append({"tool": "reranker", "status": "reranking", "candidates": len(product_map), "top_k": top_k})
            rerank_docs = []
            sid_order = []
            for sid, (product, meta) in product_map.items():
                rerank_docs.append(self._build_rerank_text(product, meta))
                sid_order.append(sid)

            ranked_indices, all_scores = await asyncio.to_thread(rerank, rerank_query, rerank_docs, top_k)

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
            steps.append({"tool": "reranker", "status": "done", "returned": len(ordered_products)})
        else:
            ordered_products = [
                (p, m, None) for p, m in product_map.values()
            ]
            steps.append({"tool": "product_retriever", "status": "done", "found": len(ordered_products), "reranked": False})

        if self.use_reranker and self.min_rerank_score is not None:
            before = len(ordered_products)
            ordered_products = [(p, m, s) for p, m, s in ordered_products if s is None or s >= self.min_rerank_score]
            dropped = before - len(ordered_products)
            if dropped:
                logger.info("Dropped {} products below min_rerank_score={}", dropped, self.min_rerank_score)

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

            product_images = [img.src for img in product.images] if product.images else []
            if image and image not in product_images:
                product_images.insert(0, image)

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
                "images": product_images,
                "price": price,
                "available": meta.get("available"),
                "available_sizes": meta.get("available_sizes", []),
                "available_colors": meta.get("available_colors", []),
                "tags": meta.get("tags", []),
            })

        steps.append({"tool": "product_retriever", "status": "done", "found": len(product_list)})
        return {"products": product_list, "steps": steps}


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