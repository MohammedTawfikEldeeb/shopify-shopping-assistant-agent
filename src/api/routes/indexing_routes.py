import requests
from fastapi import APIRouter, HTTPException, Request
from loguru import logger

from src.api.schemas.indexing import IndexStoreRequest, IndexStoreResponse
from src.api.services.store_ingestion_service import StoreIngestionService

router = APIRouter(tags=["indexing"])


@router.post("/index", response_model=IndexStoreResponse)
def index_store(payload: IndexStoreRequest, request: Request) -> IndexStoreResponse:
    service: StoreIngestionService = request.app.state.store_ingestion_service

    logger.info("Received index request for store={}", payload.store)
    try:
        result = service.ingest_store_products(payload.store)
        return IndexStoreResponse(**result)
    except ValueError as exc:
        logger.warning("Invalid index request for store={}: {}", payload.store, exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except requests.RequestException as exc:
        logger.error("Failed to fetch products for store={}: {}", payload.store, exc)
        raise HTTPException(status_code=502, detail="Failed to fetch products from Shopify") from exc
    except Exception as exc:
        logger.exception("Unexpected indexing error for store={}: {}", payload.store, exc)
        raise HTTPException(status_code=500, detail="Internal server error while indexing") from exc
