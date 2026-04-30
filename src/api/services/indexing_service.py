import re
import uuid
from html import unescape
from src.utils.embedding_service import embed_batch
from src.infrastructure.vectordb.providers.pgvector import PGVectorProvider
from src.infrastructure.vectordb.enum import PgVectorDistanceMethodEnums
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from loguru import logger
from typing import List, Dict, Any


_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")

# Fixed namespace for deterministic product UUIDs
PRODUCT_UUID_NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")


class ProductIndexingService:
    def __init__(self, db_url: str | None = None):
        if db_url is None:
            from src.config import settings
            db_url = settings.postgres.async_url

        async_engine = create_async_engine(db_url)
        async_session_factory = async_sessionmaker(async_engine, class_=AsyncSession)

        self.vector_db = PGVectorProvider(
            db_client=async_session_factory,
            default_vector_size=384,
            distance_method=PgVectorDistanceMethodEnums.COSINE.value
        )

        self.collection_name = "product_vectors"
        self.logger = logger

        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.vector_db.connect())
            else:
                loop.run_until_complete(self.vector_db.connect())
        except RuntimeError:
            asyncio.run(self.vector_db.connect())

    def _product_uuid(self, shopify_product_id: int) -> str:
        """Generate a deterministic UUID for a product based on its Shopify ID."""
        return str(uuid.uuid5(PRODUCT_UUID_NAMESPACE, str(shopify_product_id)))

    async def _ensure_collection_exists(self, vector_size: int = 384, do_reset: bool = False):
        try:
            exists = await self.vector_db.is_collection_exists(self.collection_name)
            if do_reset and exists:
                self.logger.warning(f"Dropping and recreating collection '{self.collection_name}'")
                await self.vector_db.delete_collection(self.collection_name)
                exists = False
            if not exists:
                self.logger.info(f"Creating collection '{self.collection_name}' with vector size {vector_size}")
                await self.vector_db.create_collection(
                    collection_name=self.collection_name,
                    embedding_size=vector_size,
                    do_reset=False
                )
            else:
                self.logger.debug(f"Collection '{self.collection_name}' already exists")
                await self.vector_db.create_collection(
                    collection_name=self.collection_name,
                    embedding_size=vector_size,
                    do_reset=False
                )
        except Exception as e:
            self.logger.error(f"Failed to ensure collection exists: {e}")
            raise

    def _prepare_product_text(self, product: Dict[str, Any]) -> str:
        title = product.get('title', '') or ''
        body_html = product.get('body_html', '') or ''
        description = _WHITESPACE_RE.sub(" ", unescape(_TAG_RE.sub(" ", body_html))).strip() if body_html else ''
        return f"{title}. {description}".strip() if description else title

    def _prepare_product_metadata(self, product: Dict[str, Any]) -> Dict[str, Any]:
        metadata: Dict[str, Any] = {}

        variants = product.get('variants', [])
        images = product.get('images', [])
        options = product.get('options', [])

        if variants:
            prices = []
            for v in variants:
                price_str = v.get('price')
                if price_str:
                    try:
                        prices.append(float(price_str))
                    except (ValueError, TypeError):
                        pass
            metadata['price'] = min(prices) if prices else 0.0
            metadata['available'] = any(v.get('available', False) for v in variants)
        else:
            metadata['price'] = 0.0
            metadata['available'] = False

        metadata['vendor'] = str(product.get('vendor', '')) or None
        metadata['product_type'] = str(product.get('product_type', '')) or None

        tags_raw = product.get('tags', '')
        if isinstance(tags_raw, str):
            metadata['tags'] = [t.strip() for t in tags_raw.split(',') if t.strip()]
        elif isinstance(tags_raw, list):
            metadata['tags'] = [str(t) for t in tags_raw]
        else:
            metadata['tags'] = []

        size_names = {'size', 'sizes'}
        color_names = {'color', 'colors', 'colour', 'colours'}
        sizes: set[str] = set()
        colors: set[str] = set()
        for opt in options:
            name = (opt.get('name') or '').lower().strip()
            values = opt.get('values', [])
            if name in size_names:
                sizes.update(str(v) for v in values if v)
            elif name in color_names:
                colors.update(str(v) for v in values if v)

        for v in variants:
            for key in ('option1', 'option2', 'option3'):
                val = v.get(key)
                if val:
                    val_lower = str(val).lower().strip()
                    if val_lower in colors:
                        colors.add(str(val))
                    elif val_lower in sizes:
                        sizes.add(str(val))

        metadata['available_sizes'] = sorted(sizes)
        metadata['available_colors'] = sorted(colors)

        if images:
            metadata['primary_image_url'] = str(images[0].get('src', '')) or None
            metadata['image_urls'] = [str(img.get('src', '')) for img in images if img.get('src')]
        else:
            metadata['primary_image_url'] = None
            metadata['image_urls'] = []

        shopify_id = product.get('id')
        metadata['shopify_product_id'] = shopify_id
        metadata['product_uuid'] = self._product_uuid(shopify_id) if shopify_id else None
        metadata['handle'] = product.get('handle')

        return metadata

    async def index_products(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not products:
            self.logger.warning("No products provided for indexing")
            return {
                "total_products": 0,
                "indexed_count": 0,
                "failed_count": 0,
                "errors": []
            }

        self.logger.info(f"Starting to index {len(products)} products")

        await self._ensure_collection_exists(vector_size=384, do_reset=False)

        # Build UUID -> shopify_id mapping
        product_uuids = []
        for p in products:
            sid = p.get('id')
            product_uuids.append(self._product_uuid(sid) if sid else None)

        existing_uuids = await self.vector_db.get_existing_chunk_ids(
            self.collection_name,
            [u for u in product_uuids if u is not None]
        )
        skipped = len(existing_uuids)

        texts = []
        metadatas = []
        record_ids = []
        errors = []

        for i, product in enumerate(products):
            try:
                product_uuid = product_uuids[i]
                if product_uuid is not None and product_uuid in existing_uuids:
                    continue

                text = self._prepare_product_text(product)
                if not text:
                    self.logger.warning(f"Product {i} has empty title and description, skipping")
                    errors.append(f"Product {i}: Empty title and description")
                    continue

                texts.append(text)
                metadatas.append(self._prepare_product_metadata(product))
                record_ids.append(product_uuid if product_uuid is not None else str(uuid.uuid4()))

            except Exception as e:
                self.logger.error(f"Error preparing product {i} for indexing: {e}")
                errors.append(f"Product {i}: {str(e)}")
                continue

        if not texts:
            self.logger.info(f"All {len(products)} products already indexed, nothing to do")
            return {
                "total_products": len(products),
                "indexed_count": 0,
                "skipped_count": skipped,
                "failed_count": len(errors),
                "errors": errors
            }

        try:
            self.logger.info(f"Generating embeddings for {len(texts)} new products")
            embeddings = embed_batch(texts)

            self.logger.info(f"Inserting {len(embeddings)} embedded products into vector database")
            success = await self.vector_db.insert_many(
                collection_name=self.collection_name,
                texts=texts,
                vectors=embeddings,
                metadata=metadatas,
                record_ids=record_ids,
                batch_size=50
            )

            if success:
                self.logger.info(f"Successfully indexed {len(texts)} products")
                return {
                    "total_products": len(products),
                    "indexed_count": len(texts),
                    "skipped_count": skipped,
                    "failed_count": len(errors),
                    "errors": errors
                }
            else:
                self.logger.error("Failed to insert products into vector database")
                return {
                    "total_products": len(products),
                    "indexed_count": 0,
                    "skipped_count": skipped,
                    "failed_count": len(products),
                    "errors": errors + ["Failed to insert into vector database"]
                }

        except Exception as e:
            self.logger.error(f"Error during product indexing: {e}")
            return {
                "total_products": len(products),
                "indexed_count": 0,
                "skipped_count": skipped,
                "failed_count": len(products),
                "errors": errors + [str(e)]
            }