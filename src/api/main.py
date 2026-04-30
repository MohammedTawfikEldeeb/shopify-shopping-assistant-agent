from time import perf_counter

from fastapi import FastAPI, Request
from loguru import logger
from qdrant_client import QdrantClient

from src.api.routes import indexing_router, system_router
from src.api.services import StoreIngestionService, ProductIndexingService
from src.config import settings
from src.db.factory import DBType, DatabaseFactory
from src.db.repositories.product_repository import ProductRepository
from src.utils.logger_util import setup_logging


app = FastAPI(
	title="Shopify Shopping Assistant Agent API",
	version="0.1.0",
)
app.include_router(system_router)
app.include_router(indexing_router)


@app.on_event("startup")
def on_startup() -> None:
	setup_logging()
	logger.info("Starting API service")

	# Initialize Database
	db_factory = DatabaseFactory.create(DBType.POSTGRES, settings.postgres.url)
	logger.info("Database schema management is handled by Alembic migrations")

	# Initialize Qdrant Vector DB
	qdrant_config = settings.qdrant
	try:
		if qdrant_config.environment.lower() == "cloud":
			logger.info(f"Connecting to Qdrant Cloud at {qdrant_config.url}")
			qdrant_client = QdrantClient(
				url=qdrant_config.url,
				api_key=qdrant_config.api_key,
				prefer_grpc=False,
			)
		else:
			logger.info(f"Connecting to local Qdrant at {qdrant_config.host}:{qdrant_config.port}")
			qdrant_client = QdrantClient(
				host=qdrant_config.host,
				port=qdrant_config.port,
				prefer_grpc=False,
			)
		logger.info(f"Qdrant connected successfully. Collection: {qdrant_config.collection_name}")
	except Exception as e:
		logger.error(f"Failed to connect to Qdrant: {e}")
		raise

	app.state.db_factory = db_factory
	app.state.qdrant_client = qdrant_client
	
	# Initialize repositories
	product_repository = ProductRepository(db_factory.session_factory)
	
	app.state.store_ingestion_service = StoreIngestionService(
		product_repository,
		logger=logger
	)
		
	# Initialize Product Indexing Service
	app.state.product_indexing_service = ProductIndexingService()
	logger.info("API startup complete")


@app.on_event("shutdown")
def on_shutdown() -> None:
	logger.info("Shutting down API service")


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
