"""
Step 3: Ingest fetched products into the PostgreSQL database (stores + products tables).
"""
import asyncio
from typing import Dict, List, Any

from zenml import step
from loguru import logger

from src.config import settings
from src.db.session import get_async_session_factory
from src.db.repositories.product_repository import ProductRepository


async def _ingest(store_products: dict[str, list[dict]]) -> dict[str, Any]:
    """Upsert each store and its products into the database."""
    async_sf = get_async_session_factory(settings.postgres.async_url)
    repo = ProductRepository(async_sf)

    total_ingested = 0
    total_failed = 0
    store_stats = {}

    for store_url, products in store_products.items():
        ingested = 0
        failed = 0
        for product_payload in products:
            try:
                await repo.upsert_product_from_shopify(store_url, product_payload)
                ingested += 1
            except Exception as exc:
                failed += 1
                logger.error(
                    "Failed to ingest product_id={} for store={}: {}",
                    product_payload.get("id"),
                    store_url,
                    exc,
                )
        total_ingested += ingested
        total_failed += failed
        store_stats[store_url] = {"ingested": ingested, "failed": failed}
        logger.info("Store {} — ingested={}, failed={}", store_url, ingested, failed)

    logger.info(
        "Ingestion complete — total_ingested={}, total_failed={} across {} stores",
        total_ingested,
        total_failed,
        len(store_products),
    )
    return {
        "total_stores": len(store_products),
        "total_ingested": total_ingested,
        "total_failed": total_failed,
        "store_stats": store_stats,
    }


@step
def ingest_to_db(store_products: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """ZenML step: upsert stores and products into PostgreSQL."""
    return asyncio.run(_ingest(store_products))
