from abc import ABC, abstractmethod


class VectorDBInterface(ABC):

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def disconnect(self):
        pass

    @abstractmethod
    def is_collection_exists(self, collection_name: str) -> bool:
        pass

    @abstractmethod
    def list_all_collections(self) -> list:
        pass

    @abstractmethod
    def create_collection(self, collection_name: str):
        pass

    @abstractmethod
    def delete_collection(self, collection_name: str):
        pass

    @abstractmethod
    def insert_one(self, collection_name: str, text: str, vector: list, metadata: dict):
        pass

    @abstractmethod
    def insert_many(self, collection_name: str, texts: list, vectors: list, record_ids: list, batch_size: int, metadatas: list):
        pass

    @abstractmethod
    def query(self, collection_name: str, query_vector: list, top_k: int) -> list:
        pass
