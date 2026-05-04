import asyncio
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from loguru import logger

from src.infrastructure.vectordb.providers.pgvector import PGVectorProvider
from src.utils.embedding_service import embed_query

CACHE_UUID_NAMESPACE = uuid.UUID("a3e6f8d2-7c4b-11ef-8b9a-3d2c1a0f9e87")
CACHE_COLLECTION = "semantic_cache"

DEFAULT_SIMILARITY_THRESHOLD = 0.92
DEFAULT_TTL_SECONDS = 86400


@dataclass(frozen=True)
class CacheEntry:
    query: str
    response: str
    products: list[dict]
    store_domain: str
    created_at: str

    def is_expired(self, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> bool:
        created = datetime.fromisoformat(self.created_at)
        return datetime.now(timezone.utc) > created + timedelta(seconds=ttl_seconds)


class SemanticCacheService:
    def __init__(
        self,
        vector_db: PGVectorProvider,
        *,
        similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
    ):
        self.vector_db = vector_db
        self.collection_name = CACHE_COLLECTION
        self.similarity_threshold = similarity_threshold
        self.ttl_seconds = ttl_seconds
        self.logger = logger
        self._connected = False
        self._connect_lock = asyncio.Lock()

    async def _ensure_connected(self):
        if self._connected:
            return
        async with self._connect_lock:
            if not self._connected:
                await self.vector_db.connect()
                self._connected = True

    async def _ensure_collection_exists(self):
        exists = await self.vector_db.is_collection_exists(self.collection_name)
        if not exists:
            self.logger.info("Creating semantic cache collection '{}'", self.collection_name)
            await self.vector_db.create_collection(
                collection_name=self.collection_name,
                embedding_size=384,
                do_reset=False,
            )

    async def lookup(self, query: str, store_domain: str) -> CacheEntry | None:
        await self._ensure_connected()
        await self._ensure_collection_exists()

        query_vector = await asyncio.to_thread(embed_query, query)

        results = await self.vector_db.query(
            self.collection_name,
            query_vector,
            top_k=5,
        )

        if not results:
            return None

        for result in results:
            score = result.get("score", 0.0)
            if score < self.similarity_threshold:
                continue

            metadata = result.get("payload", {}).get("metadata", {})
            if not isinstance(metadata, dict):
                metadata = json.loads(metadata) if isinstance(metadata, str) else {}

            if metadata.get("store_domain") != store_domain:
                continue

            products_raw = metadata.get("products", "[]")
            products = products_raw if isinstance(products_raw, list) else json.loads(products_raw)

            entry = CacheEntry(
                query=result.get("text", query),
                response=metadata.get("response", ""),
                products=products,
                store_domain=metadata.get("store_domain", ""),
                created_at=metadata.get("created_at", ""),
            )

            if entry.is_expired(self.ttl_seconds):
                self.logger.debug("Cache entry expired for query='{}'", query)
                continue

            self.logger.info(
                "Cache hit for query='{}' store_domain='{}' score={:.4f}",
                query, store_domain, score,
            )
            return entry

        self.logger.debug("No cache hit for query='{}' store_domain='{}'", query, store_domain)
        return None

    async def store(
        self,
        query: str,
        response: str,
        products: list[dict],
        store_domain: str,
    ) -> None:
        await self._ensure_connected()
        await self._ensure_collection_exists()

        query_vector = await asyncio.to_thread(embed_query, query)

        chunk_id = str(uuid.uuid5(CACHE_UUID_NAMESPACE, f"{store_domain}:{query}"))

        metadata = {
            "response": response,
            "products": json.dumps(products, ensure_ascii=False),
            "store_domain": store_domain,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        success = await self.vector_db.insert_one(
            collection_name=self.collection_name,
            text=query,
            vector=query_vector,
            metadata=metadata,
            record_id=chunk_id,
        )

        if success:
            self.logger.info("Cached response for query='{}' store_domain='{}'", query, store_domain)
        else:
            self.logger.warning("Failed to cache response for query='{}' store_domain='{}'", query, store_domain)

    async def clear(self, store_domain: str | None = None) -> int:
        await self._ensure_connected()
        await self._ensure_collection_exists()

        async with self.vector_db.db_client() as session:
            async with session.begin():
                if store_domain:
                    from sqlalchemy import text as sql_text
                    count_sql = sql_text(
                        f"SELECT COUNT(*) FROM {self.collection_name} "
                        f"WHERE metadata->>'store_domain' = :domain"
                    )
                    result = await session.execute(count_sql, {"domain": store_domain})
                    count = result.scalar_one()

                    delete_sql = sql_text(
                        f"DELETE FROM {self.collection_name} "
                        f"WHERE metadata->>'store_domain' = :domain"
                    )
                    await session.execute(delete_sql, {"domain": store_domain})
                else:
                    count_sql = sql_text(f"SELECT COUNT(*) FROM {self.collection_name}")
                    result = await session.execute(count_sql)
                    count = result.scalar_one()

                    delete_sql = sql_text(f"DELETE FROM {self.collection_name}")
                    await session.execute(delete_sql)

        self.logger.info("Cleared {} cache entries for store_domain='{}'", count, store_domain or "*")
        return count