from enum import Enum
from sqlalchemy import Engine
from .base import Base, create_db_engine
from .models import Product
from .repositories.product_repository import ProductRepository
from .session import create_session_factory

class DBType(Enum):
    POSTGRES = "postgresql"

class DatabaseFactory:
    _instance = None  # Singleton

    def __init__(self, db_type: DBType, connection_url: str):
        self.engine: Engine = create_db_engine(connection_url)
        self.session_factory = create_session_factory(self.engine)
        self._init_repos()

    def _init_repos(self):
        self.product_repository = ProductRepository(self.session_factory)

    def create_tables(self):
        _ = Product
        Base.metadata.create_all(self.engine)

    @classmethod
    def create(cls, db_type: DBType, url: str) -> "DatabaseFactory":
        """Factory method — swap DB by just changing db_type + url"""
        if cls._instance is None:
            cls._instance = cls(db_type, url)
        return cls._instance
