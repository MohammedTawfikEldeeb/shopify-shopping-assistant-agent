from qdrant_client import QdrantClient

from src.config import get_settings
from src.infrastructure.vectordb.enum import VectorDBEnums
from src.infrastructure.vectordb.providers.qdrant import QdrantVectorDBProvider
from src.infrastructure.vectordb.providers.pgvector import PGVectorProvider


class VectorDBFactory:
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

        if normalized_provider == VectorDBEnums.Qdrant.value:
            qdrant_settings = self.settings.qdrant
            qdrant_db_client = self._create_qdrant_client()
            return QdrantVectorDBProvider(
                client=qdrant_db_client,
                default_vector_size=qdrant_settings.vector_size,
                distance_method=qdrant_settings.distance_metric,
            )
        elif normalized_provider == VectorDBEnums.PGVector.value:
            from src.db.session import SessionLocal
            return PGVectorProvider(
                db_client=SessionLocal,
                default_vector_size=1536,
                distance_method="cosine",
            )

        raise ValueError(f"Unsupported vector database provider: {provider}")


def create_vector_db(provider: VectorDBEnums | str):
    return VectorDBFactory().create(provider)
