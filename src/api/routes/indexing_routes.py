import httpx
from fastapi import APIRouter, HTTPException, Depends
from loguru import logger

from src.api.schemas.indexing import IndexStoreRequest, IndexStoreResponse
from src.api.services.store_ingestion_service import StoreIngestionService
from src.api.services.indexing_service import ProductIndexingService
from src.api.dependencies import get_store_ingestion_service, get_product_indexing_service

router = APIRouter(tags=["indexing"])


@router.post("/index", response_model=IndexStoreResponse)
async def index_store(
    payload: IndexStoreRequest,
    ingestion_service: StoreIngestionService = Depends(get_store_ingestion_service),
    indexing_service: ProductIndexingService = Depends(get_product_indexing_service),
) -> IndexStoreResponse:
    logger.info("Received index request for store={}", payload.store)
    try:
        result = await ingestion_service.ingest_store_products(payload.store)

        products = result.pop("products", [])
        response = IndexStoreResponse(**result)

        if products:
            logger.info("Indexing {} products in vector DB", len(products))
            index_result = await indexing_service.index_products(products)
            response.vectors_indexed = index_result.get("indexed_count", 0)
            response.vectors_skipped = index_result.get("skipped_count", 0)
            response.vectors_failed = index_result.get("failed_count", 0)
            response.indexing_errors = index_result.get("errors", [])

        return response
    except ValueError as exc:
        logger.warning("Invalid index request for store={}: {}", payload.store, exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        logger.error("Failed to fetch products for store={}: {}", payload.store, exc)
        raise HTTPException(status_code=502, detail="Failed to fetch products from Shopify") from exc
    except Exception as exc:
        logger.exception("Unexpected indexing error for store={}: {}", payload.store, exc)
        raise HTTPException(status_code=500, detail="Internal server error while indexing") from exc