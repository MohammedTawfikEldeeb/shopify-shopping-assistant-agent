#!/usr/bin/env python
"""
One-time script: Clean all existing product data and vector indexes.
Run this BEFORE starting the new ZenML pipeline for the first time.

Usage:
    python -m scripts.clean_db
"""
import asyncio

from loguru import logger

from src.config import settings
from src.db.session import get_async_session_factory
from src.db.models import (
    Product, ProductVariant, ProductImage, ProductOption,
    ProductOptionValue, VariantImageLink, Store,
)
from src.db.models.session_models import UserSession, ChatMessage, AgentStateSnapshot
from src.infrastructure.vectordb.providers.pgvector import PGVectorProvider

from sqlalchemy import delete, text


async def clean():
    async_sf = get_async_session_factory(settings.postgres.async_url)

    async with async_sf() as session:
        # Product-related tables (dependency order)
        await session.execute(delete(VariantImageLink))
        await session.execute(delete(ProductOptionValue))
        await session.execute(delete(ProductOption))
        await session.execute(delete(ProductImage))
        await session.execute(delete(ProductVariant))
        await session.execute(delete(Product))
        await session.execute(delete(Store))

        # Session-related tables
        await session.execute(delete(AgentStateSnapshot))
        await session.execute(delete(ChatMessage))
        await session.execute(delete(UserSession))

        await session.commit()
        logger.info("✓ Deleted all rows from product, store, and session tables")

    # Drop vector collection
    vector_db = PGVectorProvider(
        db_client=async_sf,
        default_vector_size=384,
        distance_method="cosine",
    )
    await vector_db.connect()
    if await vector_db.is_collection_exists("product_vectors"):
        await vector_db.delete_collection("product_vectors")
        logger.info("✓ Dropped vector collection 'product_vectors'")
    else:
        logger.info("  Vector collection 'product_vectors' does not exist — nothing to drop")

    # Drop semantic cache collection if it exists
    if await vector_db.is_collection_exists("semantic_cache"):
        await vector_db.delete_collection("semantic_cache")
        logger.info("✓ Dropped vector collection 'semantic_cache'")

    logger.info("✓ Database cleanup complete — ready for fresh pipeline run")


if __name__ == "__main__":
    asyncio.run(clean())
