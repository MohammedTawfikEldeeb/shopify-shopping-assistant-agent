from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List

T = TypeVar("T")

class BaseRepository(ABC, Generic[T]):

    @abstractmethod
    def get_by_id(self, id: int) -> Optional[T]: ...

    @abstractmethod
    def get_all(self) -> List[T]: ...

    @abstractmethod
    def create(self, obj: T) -> T: ...

    @abstractmethod
    def update(self, obj: T) -> T: ...

    @abstractmethod
    def delete(self, id: int) -> bool: ...