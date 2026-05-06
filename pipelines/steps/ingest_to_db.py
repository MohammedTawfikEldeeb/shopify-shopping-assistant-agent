"""
Step 3: Ingest fetched products into the PostgreSQL database (stores + products tables).
"""
import asyncio
from typing import Dict, List, Any

from zenml import step
from loguru import logger
from sqlalchemy import text

from src.config import settings
from src.db.session import get_async_session, create_async_session_factory
from src.db.repositories.product_repository import ProductRepository


async def _verify_related_counts(session_factory) -> dict[str, int]:
    """Run COUNT(*) on all related tables to verify ingestion."""
    async with get_async_session(session_factory) as session:
        product_count = await session.scalar(text("SELECT COUNT(*) FROM products"))
        variant_count = await session.scalar(text("SELECT COUNT(*) FROM product_variants"))
        image_count = await session.scalar(text("SELECT COUNT(*) FROM product_images"))
        option_count = await session.scalar(text("SELECT COUNT(*) FROM product_options"))
        option_value_count = await session.scalar(text("SELECT COUNT(*) FROM product_option_values"))
        return {
            "products": product_count or 0,
            "variants": variant_count or 0,
            "images": image_count or 0,
            "options": option_count or 0,
            "option_values": option_value_count or 0,
        }


async def _ingest(store_products: dict[str, list[dict]]) -> dict[str, Any]:
    """Upsert each store and its products into the database."""
    async_sf = create_async_session_factory(settings.postgres.async_url)
    repo = ProductRepository(async_sf)

    total_ingested = 0
    total_failed = 0
    store_stats = {}

    for store_url, products in store_products.items():
        # Debug: log payload structure of first product
        if products:
            first = products[0]
            logger.info(
                "First product payload keys={} has_variants={} has_images={} has_options={}",
                list(first.keys()),
                "variants" in first and bool(first.get("variants")),
                "images" in first and bool(first.get("images")),
                "options" in first and bool(first.get("options")),
            )

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

    counts = await _verify_related_counts(async_sf)
    logger.info(
        "Post-ingest verification — products={}, variants={}, images={}, options={}, option_values={}",
        counts["products"],
        counts["variants"],
        counts["images"],
        counts["options"],
        counts["option_values"],
    )

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
        "db_counts": counts,
    }


@step
def ingest_to_db(store_products: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """ZenML step: upsert stores and products into PostgreSQL."""
    return asyncio.run(_ingest(store_products))
