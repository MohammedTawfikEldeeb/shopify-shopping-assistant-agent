from qdrant_client import QdrantClient

from src.config import get_settings
from src.infrastructure.vectordb.enum import VectorDBEnums
from src.infrastructure.vectordb.providers.qdrant import QdrantVectorDBProvider
from src.infrastructure.vectordb.providers.pgvector import PGVectorProvider


class VectorDBFactory:
    _instance = None
    _cache = {}

    def __init__(self) -> None:
        self.settings = get_settings()

    def _create_qdrant_client(self) -> QdrantClient:
        qdrant_settings = self.settings.qdrant
        client_kwargs = {
            "api_key": qdrant_settings.api_key,
            "prefer_grpc": qdrant_settings.prefer_grpc,
        }

        if qdrant_settings.url:
            client_kwargs["url"] = qdrant_settings.url
        else:
            client_kwargs["host"] = qdrant_settings.host
            client_kwargs["port"] = qdrant_settings.port
            client_kwargs["https"] = qdrant_settings.https

        return QdrantClient(**client_kwargs)

    def create(self, provider: VectorDBEnums | str):
        normalized_provider = provider.value if isinstance(provider, VectorDBEnums) else str(provider).upper()

        if normalized_provider in self._cache:
            return self._cache[normalized_provider]

        if normalized_provider == VectorDBEnums.Qdrant.value:
            qdrant_settings = self.settings.qdrant
            qdrant_db_client = self._create_qdrant_client()
            provider_instance = QdrantVectorDBProvider(
                client=qdrant_db_client,
                default_vector_size=qdrant_settings.vector_size,
                distance_method=qdrant_settings.distance_metric,
            )
        elif normalized_provider == VectorDBEnums.PGVector.value:
            from src.db.factory import DatabaseFactory
            db_factory = DatabaseFactory.get_instance()
            if db_factory is None:
                raise RuntimeError(
                    "DatabaseFactory has not been initialized. "
                    "Call DatabaseFactory.create() during application startup before creating vector DB providers."
                )
            provider_instance = PGVectorProvider(
                db_client=db_factory.async_session_factory,
                default_vector_size=1536,
                distance_method="cosine",
            )
        else:
            raise ValueError(f"Unsupported vector database provider: {provider}")

        self._cache[normalized_provider] = provider_instance
        return provider_instance

    def register(self, provider: VectorDBEnums | str, instance):
        """Register a pre-created provider instance (used during app startup to share connections)."""
        normalized_provider = provider.value if isinstance(provider, VectorDBEnums) else str(provider).upper()
        self._cache[normalized_provider] = instance

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls):
        cls._instance = None
        cls._cache.clear()


def create_vector_db(provider: VectorDBEnums | str):
    return VectorDBFactory.get_instance().create(provider)
