from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import requests
from loguru import logger as default_logger

from src.db.repositories.product_repository import ProductRepository


@dataclass(frozen=True)
class NormalizedStore:
    domain: str
    base_url: str
    products_url: str


class StoreIngestionService:
    def __init__(
        self,
        product_repository: ProductRepository,
        *,
        logger=default_logger,
        timeout_seconds: int = 30,
    ) -> None:
        self._product_repository = product_repository
        self._logger = logger
        self._timeout_seconds = timeout_seconds

    def ingest_store_products(self, store_input: str) -> dict[str, Any]:
        normalized_store = self._normalize_store_input(store_input)
        self._logger.info(
            "Starting store ingestion for domain={} from {}",
            normalized_store.domain,
            normalized_store.products_url,
        )

        products = self._fetch_products(normalized_store.products_url)
        ingested_count = 0
        failed_count = 0

        for product_payload in products:
            try:
                self._product_repository.upsert_product_from_shopify(
                    normalized_store.base_url,
                    product_payload,
                )
                ingested_count += 1
            except Exception as exc:
                failed_count += 1
                self._logger.exception(
                    "Failed to upsert product_id={} for domain={}: {}",
                    product_payload.get("id"),
                    normalized_store.domain,
                    exc,
                )

        self._logger.info(
            "Store ingestion complete for domain={} total={} ingested={} failed={}",
            normalized_store.domain,
            len(products),
            ingested_count,
            failed_count,
        )

        return {
            "store_domain": normalized_store.domain,
            "store_base_url": normalized_store.base_url,
            "products_url": normalized_store.products_url,
            "total_products_received": len(products),
            "products_ingested": ingested_count,
            "products_failed": failed_count,
        }

    def _fetch_products(self, products_url: str) -> list[dict[str, Any]]:
        self._logger.info("Fetching Shopify products from {}", products_url)
        response = requests.get(products_url, timeout=self._timeout_seconds)
        response.raise_for_status()

        payload = response.json()
        products = payload.get("products", [])
        if not isinstance(products, list):
            raise ValueError("Invalid Shopify payload: 'products' must be a list")

        self._logger.info("Fetched {} products from {}", len(products), products_url)
        return [item for item in products if isinstance(item, dict)]

    @staticmethod
    def _normalize_store_input(store_input: str) -> NormalizedStore:
        value = store_input.strip()
        if not value:
            raise ValueError("Store input is required")

        parsed = urlparse(value if "://" in value else f"https://{value}")
        domain = (parsed.netloc or parsed.path).lower().strip("/")

        if not domain:
            raise ValueError("Unable to parse store domain from input")

        base_url = f"https://{domain}"
        products_url = f"{base_url}/products.json"
        return NormalizedStore(domain=domain, base_url=base_url, products_url=products_url)
