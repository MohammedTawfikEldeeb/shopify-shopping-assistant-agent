from enum import Enum
from sqlalchemy import Engine
from sqlalchemy.ext.asyncio import AsyncEngine
from .base import Base
from .models import Product
from .repositories.product_repository import ProductRepository
from .session import get_sync_engine, get_sync_session_factory, get_async_engine, get_async_session_factory

class DBType(Enum):
    POSTGRES = "postgresql"

class DatabaseFactory:
    _instance = None  # Singleton

    def __init__(self, db_type: DBType, sync_url: str, async_url: str):
        self.sync_url = sync_url
        self.async_url = async_url
        self.engine: Engine = get_sync_engine(sync_url)
        self.session_factory = get_sync_session_factory(sync_url)
        self.async_engine: AsyncEngine = get_async_engine(async_url)
        self.async_session_factory = get_async_session_factory(async_url)
        self._init_repos()

    def _init_repos(self):
        self.product_repository = ProductRepository(self.session_factory)

    def create_tables(self):
        _ = Product
        Base.metadata.create_all(self.engine)

    @classmethod
    def create(cls, db_type: DBType, sync_url: str, async_url: str | None = None) -> "DatabaseFactory":
        """Factory method — swap DB by just changing db_type + url"""
        if cls._instance is None:
            cls._instance = cls(db_type, sync_url, async_url or sync_url)
        return cls._instance

    @classmethod
    def get_instance(cls) -> "DatabaseFactory | None":
        return cls._instance

    @classmethod
    def reset(cls):
        cls._instance = None
