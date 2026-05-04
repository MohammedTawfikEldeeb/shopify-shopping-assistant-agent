from __future__ import annotations

import re
import uuid
from datetime import datetime
from decimal import Decimal
from html import unescape
from typing import Any, Optional
from urllib.parse import urlparse

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..interfaces.base_repository import BaseRepository
from ..models import (
    Product,
    ProductImage,
    ProductOption,
    ProductOptionValue,
    ProductVariant,
    Store,
    SyncStatus,
    VariantImageLink,
)
from ..session import get_async_session


TAG_RE = re.compile(r"<[^>]+>")
WHITESPACE_RE = re.compile(r"\s+")


class ProductRepository(BaseRepository[Product]):
    def __init__(self, async_session_factory: async_sessionmaker):
        self.async_session_factory = async_session_factory

    async def get_by_id(self, id: uuid.UUID) -> Optional[Product]:
        async with get_async_session(self.async_session_factory) as session:
            return await session.get(Product, id)

    async def get_all(self) -> list[Product]:
        async with get_async_session(self.async_session_factory) as session:
            result = await session.scalars(select(Product))
            return list(result.all())

    async def create(self, obj: Product) -> Product:
        async with get_async_session(self.async_session_factory) as session:
            session.add(obj)
            await session.flush()
            await session.refresh(obj)
            return obj

    async def update(self, obj: Product) -> Product:
        async with get_async_session(self.async_session_factory) as session:
            merged = await session.merge(obj)
            await session.flush()
            await session.refresh(merged)
            return merged

    async def delete(self, id: uuid.UUID) -> bool:
        async with get_async_session(self.async_session_factory) as session:
            product = await session.get(Product, id)
            if product is None:
                return False
            await session.delete(product)
            return True

    async def get_store_by_domain(self, domain: str) -> Optional[Store]:
        async with get_async_session(self.async_session_factory) as session:
            return await session.scalar(select(Store).where(Store.domain == self._normalize_domain(domain)))

    async def get_store_id_by_domain(self, domain: str) -> Optional[uuid.UUID]:
        """Get store ID by domain (returns just the ID to avoid detached instance issues)"""
        async with get_async_session(self.async_session_factory) as session:
            store = await session.scalar(select(Store).where(Store.domain == self._normalize_domain(domain)))
            return store.id if store else None

    async def upsert_store_and_get_id(
        self,
        domain_or_url: str,
        *,
        shop_name: str | None = None,
        currency_code: str | None = None,
        raw_metadata: dict[str, Any] | None = None,
    ) -> uuid.UUID:
        """Upsert store and return just the ID to avoid detached instance issues"""
        async with get_async_session(self.async_session_factory) as session:
            store = await self._upsert_store_in_session(
                session,
                domain_or_url=domain_or_url,
                shop_name=shop_name,
                currency_code=currency_code,
                raw_metadata=raw_metadata,
            )
            await session.flush()
            store_id = store.id
            return store_id

    async def upsert_store(
        self,
        domain_or_url: str,
        *,
        shop_name: str | None = None,
        currency_code: str | None = None,
        raw_metadata: dict[str, Any] | None = None,
    ) -> Store:
        async with get_async_session(self.async_session_factory) as session:
            store = await self._upsert_store_in_session(
                session,
                domain_or_url=domain_or_url,
                shop_name=shop_name,
                currency_code=currency_code,
                raw_metadata=raw_metadata,
            )
            await session.flush()
            await session.refresh(store)
            return store

    async def upsert_product_from_shopify(self, store_url: str, payload: dict[str, Any]) -> Product:
        async with get_async_session(self.async_session_factory) as session:
            store = await self._upsert_store_in_session(session, domain_or_url=store_url)
            product = await self._upsert_product_in_session(session, store=store, payload=payload)
            store.last_synced_at = datetime.now().astimezone()
            await session.flush()
            await session.refresh(product)
            return product

    async def _upsert_store_in_session(
        self,
        session: AsyncSession,
        *,
        domain_or_url: str,
        shop_name: str | None = None,
        currency_code: str | None = None,
        raw_metadata: dict[str, Any] | None = None,
    ) -> Store:
        domain = self._normalize_domain(domain_or_url)
        base_url = self._normalize_base_url(domain_or_url)
        store = await session.scalar(select(Store).where(Store.domain == domain))

        if store is None:
            store = Store(domain=domain, base_url=base_url)
            session.add(store)

        store.base_url = base_url
        if shop_name:
            store.shop_name = shop_name
        if currency_code:
            store.currency_code = currency_code
        if raw_metadata is not None:
            store.raw_metadata = raw_metadata
        return store

    async def _upsert_product_in_session(self, session: AsyncSession, *, store: Store, payload: dict[str, Any]) -> Product:
        shopify_product_id = int(payload["id"])
        product = await session.scalar(
            select(Product).where(
                Product.store_id == store.id,
                Product.shopify_product_id == shopify_product_id,
            )
        )

        if product is None:
            product = Product(store=store, shopify_product_id=shopify_product_id)
            session.add(product)

        product.handle = payload.get("handle") or str(shopify_product_id)
        product.title = payload.get("title") or product.handle
        clean_source = payload.get("body_html") or payload.get("body_text")
        product.description = self._html_to_text(clean_source)
        product.vendor = payload.get("vendor")
        product.product_type = payload.get("product_type")
        product.published_at = self._parse_dt(payload.get("published_at"))
        product.shopify_created_at = self._parse_dt(payload.get("created_at"))
        product.shopify_updated_at = self._parse_dt(payload.get("updated_at"))
        product.sync_status = SyncStatus.SYNCED
        product.raw_payload = payload

        await session.flush()

        await self._replace_options(session, product, payload.get("options", []))
        image_map = await self._replace_images(session, product, payload.get("images", []))
        await self._replace_variants(session, product, payload.get("variants", []), image_map=image_map)

        return product

    async def _replace_options(self, session: AsyncSession, product: Product, options: list[dict[str, Any]]) -> None:
        await session.execute(delete(ProductOptionValue).where(ProductOptionValue.option_id.in_(select(ProductOption.id).where(ProductOption.product_id == product.id))))
        await session.execute(delete(ProductOption).where(ProductOption.product_id == product.id))

        for option_payload in options:
            option = ProductOption(
                product=product,
                name=option_payload.get("name") or "Option",
                position=option_payload.get("position"),
            )
            session.add(option)
            await session.flush()
            for index, value in enumerate(option_payload.get("values", []), start=1):
                session.add(ProductOptionValue(option=option, value=str(value), position=index))

    async def _replace_images(
        self, session: AsyncSession, product: Product, images: list[dict[str, Any]]
    ) -> dict[int, ProductImage]:
        await session.execute(delete(VariantImageLink).where(VariantImageLink.image_id.in_(select(ProductImage.id).where(ProductImage.product_id == product.id))))
        await session.execute(delete(ProductImage).where(ProductImage.product_id == product.id))

        image_map: dict[int, ProductImage] = {}
        for image_payload in images:
            image = ProductImage(
                product=product,
                shopify_image_id=int(image_payload["id"]),
                src=image_payload.get("src") or "",
                alt_text=image_payload.get("alt"),
                position=image_payload.get("position"),
                width=image_payload.get("width"),
                height=image_payload.get("height"),
                shopify_created_at=self._parse_dt(image_payload.get("created_at")),
                shopify_updated_at=self._parse_dt(image_payload.get("updated_at")),
                raw_payload=image_payload,
            )
            session.add(image)
            await session.flush()
            image_map[image.shopify_image_id] = image
        return image_map

    async def _replace_variants(
        self,
        session: AsyncSession,
        product: Product,
        variants: list[dict[str, Any]],
        *,
        image_map: dict[int, ProductImage],
    ) -> None:
        await session.execute(delete(VariantImageLink).where(VariantImageLink.variant_id.in_(select(ProductVariant.id).where(ProductVariant.product_id == product.id))))
        await session.execute(delete(ProductVariant).where(ProductVariant.product_id == product.id))

        for variant_payload in variants:
            variant = ProductVariant(
                product=product,
                shopify_variant_id=int(variant_payload["id"]),
                title=variant_payload.get("title") or "",
                sku=variant_payload.get("sku"),
                option1=variant_payload.get("option1"),
                option2=variant_payload.get("option2"),
                option3=variant_payload.get("option3"),
                available=bool(variant_payload.get("available")),
                price=self._to_decimal(variant_payload.get("price")),
                compare_at_price=self._to_decimal(variant_payload.get("compare_at_price")),
                requires_shipping=variant_payload.get("requires_shipping"),
                taxable=variant_payload.get("taxable"),
                grams=variant_payload.get("grams"),
                position=variant_payload.get("position"),
                shopify_created_at=self._parse_dt(variant_payload.get("created_at")),
                shopify_updated_at=self._parse_dt(variant_payload.get("updated_at")),
                raw_payload=variant_payload,
            )
            session.add(variant)
            await session.flush()

            featured_image = variant_payload.get("featured_image") or {}
            featured_image_id = featured_image.get("id")
            if featured_image_id and int(featured_image_id) in image_map:
                session.add(VariantImageLink(variant=variant, image=image_map[int(featured_image_id)]))

    @staticmethod
    def _normalize_domain(domain_or_url: str) -> str:
        value = domain_or_url.strip()
        parsed = urlparse(value if "://" in value else f"https://{value}")
        return parsed.netloc.lower() or parsed.path.lower().strip("/")

    @staticmethod
    def _normalize_base_url(domain_or_url: str) -> str:
        domain = ProductRepository._normalize_domain(domain_or_url)
        return f"https://{domain}"

    @staticmethod
    def _html_to_text(value: str | None) -> str | None:
        if not value:
            return None
        text = unescape(TAG_RE.sub(" ", value))
        return WHITESPACE_RE.sub(" ", text).strip()

    @staticmethod
    def _parse_dt(value: str | None) -> datetime | None:
        if not value:
            return None
        return datetime.fromisoformat(value)

    @staticmethod
    def _to_decimal(value: Any) -> Decimal | None:
        if value in (None, ""):
            return None
        return Decimal(str(value))