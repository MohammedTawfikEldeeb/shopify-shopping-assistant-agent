from typing import Any
from uuid import uuid4

from qdrant_client import QdrantClient
from qdrant_client.http import models

from src.config import get_settings
from src.infrastructure.vectordb.enum import DistanceMetric
from src.infrastructure.vectordb.interface import VectorDBInterface


class QdrantVectorDBProvider(VectorDBInterface):
    def __init__(
        self,
        client: QdrantClient,
        default_vector_size: int | None = None,
        distance_method: str | DistanceMetric | None = None,
    ) :
        self.client = client
        self.vector_size = default_vector_size or get_settings().qdrant.vector_size
        self.distance_method = models.Distance.COSINE
        if distance_method == DistanceMetric.COSINE.value:
            self.distance_method = models.Distance.COSINE
        elif distance_method == DistanceMetric.DOT_PRODUCT.value:
            self.distance_method = models.Distance.DOT

    def connect(self):
        return self.client

    def disconnect(self):
        if self.client is not None:
            self.client.close()
            self.client = None

    def is_collection_exists(self, collection_name: str) -> bool:
    
        return self.client.collection_exists(collection_name)

    def list_all_collections(self) -> list:

        collections = self.client.get_collections().collections
        return [collection.name for collection in collections]

    def create_collection(self, collection_name: str):

        if self.is_collection_exists(collection_name):
            return

        self.client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=self.vector_size,
                distance=self.distance_method,
            ),
        )

    def delete_collection(self, collection_name: str):

        if self.is_collection_exists(collection_name):
            self.client.delete_collection(collection_name=collection_name)

    def insert_one(self, collection_name: str, text: str, vector: list, metadata: dict):

        payload = self._build_payload(text=text, metadata=metadata)
        point = models.PointStruct(id=str(uuid4()), vector=vector, payload=payload)
        self.client.upsert(collection_name=collection_name, points=[point], wait=True)

    def insert_many(self, collection_name: str, texts: list, vectors: list, record_ids: list, batch_size: int, metadatas: list):


        if not (len(texts) == len(vectors) == len(record_ids) == len(metadatas)):
            raise ValueError("texts, vectors, record_ids, and metadatas must have the same length")

        batch_size = max(1, batch_size)
        for start in range(0, len(texts), batch_size):
            end = start + batch_size
            points = [
                models.PointStruct(
                    id=record_id,
                    vector=vector,
                    payload=self._build_payload(text=text, metadata=metadata),
                )
                for record_id, text, vector, metadata in zip(
                    record_ids[start:end],
                    texts[start:end],
                    vectors[start:end],
                    metadatas[start:end],
                    strict=False,
                )
            ]
            self.client.upsert(collection_name=collection_name, points=points, wait=True)

    def query(self, collection_name: str, query_vector: list, top_k: int) -> list:

        results = self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=top_k,
            with_payload=True,
            with_vectors=False,
        )
        return [
            {
                "id": result.id,
                "score": result.score,
                "payload": result.payload,
            }
            for result in results
        ]

    @staticmethod
    def _build_payload(text: str, metadata: dict | None) -> dict[str, Any]:
        payload = {"text": text}
        if metadata:
            payload["metadata"] = metadata
        return payload


 
