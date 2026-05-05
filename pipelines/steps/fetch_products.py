"""
Step 2: Probe every store's /products.json and fetch products from accessible ones.
Returns a dict mapping store_url -> list of raw product payloads.
"""
import asyncio
from typing import Dict, List, Any

import httpx
from zenml import step
from loguru import logger

from pipelines.stores import STORES


async def _fetch_store(client: httpx.AsyncClient, store_url: str) -> tuple[str, list[dict]]:
    """Try to GET /products.json; return (store_url, products) or (store_url, [])."""
    url = f"{store_url.rstrip('/')}/products.json"
    try:
        resp = await client.get(url, follow_redirects=True)
        if resp.status_code != 200:
            logger.warning("Store {} returned HTTP {} — skipping", store_url, resp.status_code)
            return store_url, []
        data = resp.json()
        products = data.get("products", [])
        if not isinstance(products, list):
            logger.warning("Store {} returned invalid payload — skipping", store_url)
            return store_url, []
        logger.info("Store {} — fetched {} products", store_url, len(products))
        return store_url, [p for p in products if isinstance(p, dict)]
    except httpx.TimeoutException:
        logger.warning("Store {} timed out — skipping", store_url)
        return store_url, []
    except Exception as exc:
        logger.warning("Store {} fetch error: {} — skipping", store_url, exc)
        return store_url, []


async def _fetch_all() -> dict[str, list[dict]]:
    """Concurrently probe all stores (limit concurrency to 10)."""
    semaphore = asyncio.Semaphore(10)
    result: dict[str, list[dict]] = {}

    async def _limited_fetch(client: httpx.AsyncClient, store_url: str):
        async with semaphore:
            url, products = await _fetch_store(client, store_url)
            result[url] = products

    async with httpx.AsyncClient(timeout=30, headers={"User-Agent": "ShopifyAssistantBot/1.0"}) as client:
        tasks = [_limited_fetch(client, s) for s in STORES]
        await asyncio.gather(*tasks)

    accessible = {k: v for k, v in result.items() if v}
    skipped = {k for k, v in result.items() if not v}
    logger.info(
        "Fetch complete — {} accessible stores, {} skipped",
        len(accessible),
        len(skipped),
    )
    if skipped:
        logger.info("Skipped stores: {}", ", ".join(sorted(skipped)))
    return accessible


@step
def fetch_products() -> Dict[str, List[Dict[str, Any]]]:
    """ZenML step: fetch products.json from all stores. Skip inaccessible ones."""
    return asyncio.run(_fetch_all())
