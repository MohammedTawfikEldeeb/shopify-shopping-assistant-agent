from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

def create_db_engine(url: str, **kwargs):
    return create_engine(url, **kwargs)