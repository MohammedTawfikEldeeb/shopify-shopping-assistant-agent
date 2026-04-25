from time import perf_counter

from fastapi import FastAPI, Request
from loguru import logger

from src.api.routes import indexing_router, system_router
from src.api.services import StoreIngestionService
from src.config import settings
from src.db.factory import DBType, DatabaseFactory
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

	db_factory = DatabaseFactory.create(DBType.POSTGRES, settings.postgres.url)
	logger.info("Database schema management is handled by Alembic migrations")

	app.state.db_factory = db_factory
	app.state.store_ingestion_service = StoreIngestionService(db_factory.product_repository, logger=logger)
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
