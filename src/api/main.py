from contextlib import asynccontextmanager
from time import perf_counter

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from src.agent import ShoppingAgent
from src.agent.tools import ProductRetriever, SQLQueryTool
from src.api.routes import chat_router, system_router
from src.api.services.semantic_cache_service import SemanticCacheService
from src.config import settings
from src.db.factory import DBType, DatabaseFactory
from src.db.repositories.session_repository import (
    AgentStateSnapshotRepository,
    ChatMessageRepository,
    UserSessionRepository,
)
from src.infrastructure.vectordb.enum import VectorDBEnums
from src.infrastructure.vectordb.factory import VectorDBFactory
from src.infrastructure.vectordb.providers.pgvector import PGVectorProvider
from src.utils.embedding_service import embed_query
from src.utils.logger_util import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Starting API service")

    # Initialize Database (singleton — both sync and async engines)
    db_factory = DatabaseFactory.create(
        DBType.POSTGRES,
        settings.postgres.url,
        settings.postgres.async_url,
    )
    logger.info("Database schema management is handled by Alembic migrations")

    vector_db_factory = VectorDBFactory.get_instance()

    app.state.db_factory = db_factory

    # Shared PGVector provider (reused across services to avoid multiple async engines)
    shared_vector_db = PGVectorProvider(
        db_client=db_factory.async_session_factory,
        default_vector_size=384,
        distance_method="cosine",
    )

    # Connect PGVector provider (create vector extension if needed)
    await shared_vector_db.connect()

    # Register PGVector provider in factory
    vector_db_factory.register(VectorDBEnums.PGVector, shared_vector_db)

    # Initialize semantic cache (optional, controlled by config)
    semantic_cache_service = None
    if settings.semantic_cache.enabled:
        semantic_cache_service = SemanticCacheService(
            vector_db=shared_vector_db,
            similarity_threshold=settings.semantic_cache.similarity_threshold,
            ttl_seconds=settings.semantic_cache.ttl_seconds,
        )
        logger.info(
            "Semantic caching enabled (threshold={}, ttl={}s)",
            settings.semantic_cache.similarity_threshold,
            settings.semantic_cache.ttl_seconds,
        )
    else:
        logger.info("Semantic caching disabled by configuration")
    app.state.semantic_cache_service = semantic_cache_service

    # Initialize repositories — all use async session factory
    user_session_repository = UserSessionRepository(db_factory.async_session_factory)
    chat_message_repository = ChatMessageRepository(db_factory.async_session_factory)
    agent_state_repository = AgentStateSnapshotRepository(db_factory.async_session_factory)

    app.state.user_session_repository = user_session_repository
    app.state.chat_message_repository = chat_message_repository
    app.state.agent_state_repository = agent_state_repository

    # Initialize Shopping Agent with shared retriever + SQL tool (all async)
    retriever = ProductRetriever(
        vector_db=shared_vector_db,
        async_session_factory=db_factory.async_session_factory,
    )
    sql_tool = SQLQueryTool(async_session_factory=db_factory.async_session_factory)
    app.state.shopping_agent = ShoppingAgent(
        retriever=retriever,
        sql_tool=sql_tool,
    )
    logger.info("Shopping agent initialized")

    # Warm up embedding model
    logger.info("Warming up embedding model...")
    embed_query("warmup")
    logger.info("Embedding model ready")

    logger.info("API startup complete — chat-only mode (indexing via ZenML pipeline)")

    yield

    # Shutdown
    logger.info("Shutting down API service")


app = FastAPI(
    title="Shopify Shopping Assistant Agent API",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(system_router)
app.include_router(chat_router)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = perf_counter()
    logger.info("Incoming request method={} path={}", request.method, request.url.path)

    try:
        response = await call_next(request)
    except Exception as exc:
        logger.exception(
            "Request failed method={} path={} error={}",
            request.method,
            request.url.path,
            exc,
        )
        raise

    duration_ms = (perf_counter() - start_time) * 1000
    logger.info(
        "Completed request method={} path={} status={} duration_ms={:.2f}",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response
