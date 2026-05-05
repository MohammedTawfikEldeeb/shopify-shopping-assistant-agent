"""
ZenML pipeline: Shopify Store Ingestion & Indexing

Flow:
  1. fetch_products     — probe all stores, fetch /products.json
  2. ingest_to_db       — upsert stores + products into PostgreSQL
  3. index_to_vectordb  — generate embeddings + insert into PGVector
"""
from zenml import pipeline

from pipelines.steps.fetch_products import fetch_products
from pipelines.steps.ingest_to_db import ingest_to_db
from pipelines.steps.index_to_vectordb import index_to_vectordb


@pipeline(name="shopify_ingestion_pipeline")
def shopify_ingestion_pipeline():
    """Fetch products from all Shopify stores, ingest into DB, and index."""
    store_products = fetch_products()
    ingest_result = ingest_to_db(store_products)
    index_result = index_to_vectordb(store_products, ingest_result)
    return index_result
