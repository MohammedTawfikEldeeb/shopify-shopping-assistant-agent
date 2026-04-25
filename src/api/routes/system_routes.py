from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def root() -> dict[str, str]:
    return {
        "service": "shopify-shopping-assistant-agent",
        "status": "ok",
    }


@router.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
