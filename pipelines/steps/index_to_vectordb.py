"""
Step 4: Index all fetched products into the PGVector vector database.
"""
import asyncio
from typing import Dict, List, Any

from zenml import step
from loguru import logger

from src.config import settings
from src.db.session import create_async_session_factory
from src.infrastructure.vectordb.providers.pgvector import PGVectorProvider
from src.api.services.indexing_service import ProductIndexingService

from urllib.parse import urlparse


def _extract_domain(store_url: str) -> str:
    parsed = urlparse(store_url if "://" in store_url else f"https://{store_url}")
    return (parsed.netloc or parsed.path).lower().strip("/")


async def _index(store_products: dict[str, list[dict]], ingest_result: dict) -> dict[str, Any]:
    """Create embeddings and insert into vector DB for all products."""
    async_sf = create_async_session_factory(settings.postgres.async_url)
    vector_db = PGVectorProvider(
        db_client=async_sf,
        default_vector_size=384,
        distance_method="cosine",
    )

    indexing_service = ProductIndexingService(vector_db=vector_db)

    total_indexed = 0
    total_skipped = 0
    total_failed = 0
    all_errors = []

    for store_url, products in store_products.items():
        if not products:
            continue
        domain = _extract_domain(store_url)
        logger.info("Indexing {} products for store {}", len(products), domain)
        result = await indexing_service.index_products(products)
        total_indexed += result.get("indexed_count", 0)
        total_skipped += result.get("skipped_count", 0)
        total_failed += result.get("failed_count", 0)
        all_errors.extend(result.get("errors", []))

    logger.info(
        "Indexing complete — indexed={}, skipped={}, failed={}",
        total_indexed,
        total_skipped,
        total_failed,
    )
    return {
        "total_indexed": total_indexed,
        "total_skipped": total_skipped,
        "total_failed": total_failed,
        "errors": all_errors[:50],  # Cap to avoid huge artifacts
    }


@step
def index_to_vectordb(
    store_products: Dict[str, List[Dict[str, Any]]],
    ingest_result: Dict[str, Any],
) -> Dict[str, Any]:
    """ZenML step: generate embeddings and insert into PGVector."""
    return asyncio.run(_index(store_products, ingest_result))
