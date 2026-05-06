from contextlib import asynccontextmanager, contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker


# Sync (kept for Alembic migrations and the test.py utility only)
_sync_engine = None
_sync_session_factory = None

# Async
_async_engine = None
_async_session_factory = None


def get_sync_engine(url: str, **kwargs):
    global _sync_engine
    if _sync_engine is None:
        _sync_engine = create_engine(url, **kwargs)
    return _sync_engine


def get_sync_session_factory(url: str, **kwargs):
    global _sync_session_factory
    if _sync_session_factory is None:
        engine = get_sync_engine(url, **kwargs)
        _sync_session_factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    return _sync_session_factory


def get_async_engine(url: str, **kwargs):
    global _async_engine
    if _async_engine is None:
        _async_engine = create_async_engine(url, **kwargs)
    return _async_engine


def get_async_session_factory(url: str, **kwargs):
    global _async_session_factory
    if _async_session_factory is None:
        engine = get_async_engine(url, **kwargs)
        _async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return _async_session_factory


def create_async_session_factory(url: str, **kwargs):
    """Create a new async session factory without using cached engine (safe for new event loops)."""
    engine = create_async_engine(url, **kwargs)
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@contextmanager
def get_session(session_factory) -> Session:
    """Sync context manager — kept only for Alembic / offline scripts."""
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@asynccontextmanager
async def get_async_session(session_factory):
    """Async context manager used by all runtime code."""
    session = session_factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
