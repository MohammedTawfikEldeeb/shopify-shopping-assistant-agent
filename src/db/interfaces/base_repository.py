import uuid
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List

T = TypeVar("T")

class BaseRepository(ABC, Generic[T]):

    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> Optional[T]: ...

    @abstractmethod
    async def get_all(self) -> List[T]: ...

    @abstractmethod
    async def create(self, obj: T) -> T: ...

    @abstractmethod
    async def update(self, obj: T) -> T: ...

    @abstractmethod
    async def delete(self, id: uuid.UUID) -> bool: ...