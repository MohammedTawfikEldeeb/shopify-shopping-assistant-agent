from __future__ import annotations

import re
import uuid
from datetime import datetime
from decimal import Decimal
from html import unescape
from typing import Any, Optional
from urllib.parse import urlparse

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker

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
from ..session import get_session


TAG_RE = re.compile(r"<[^>]+>")
WHITESPACE_RE = re.compile(r"\s+")


class ProductRepository(BaseRepository[Product]):
    def __init__(self, session_factory: sessionmaker):
        self.session_factory = session_factory

    def get_by_id(self, id: uuid.UUID) -> Optional[Product]:
        with get_session(self.session_factory) as session:
            return session.get(Product, id)

    def get_all(self) -> list[Product]:
        with get_session(self.session_factory) as session:
            return list(session.scalars(select(Product)).all())

    def create(self, obj: Product) -> Product:
        with get_session(self.session_factory) as session:
            session.add(obj)
            session.flush()
            session.refresh(obj)
            return obj

    def update(self, obj: Product) -> Product:
        with get_session(self.session_factory) as session:
            merged = session.merge(obj)
            session.flush()
            session.refresh(merged)
            return merged

    def delete(self, id: uuid.UUID) -> bool:
        with get_session(self.session_factory) as session:
            product = session.get(Product, id)
            if product is None:
                return False
            session.delete(product)
            return True

    def get_store_by_domain(self, domain: str) -> Optional[Store]:
        with get_session(self.session_factory) as session:
            return session.scalar(select(Store).where(Store.domain == self._normalize_domain(domain)))

    def get_store_id_by_domain(self, domain: str) -> Optional[uuid.UUID]:
        """Get store ID by domain (returns just the ID to avoid detached instance issues)"""
        with get_session(self.session_factory) as session:
            store = session.scalar(select(Store).where(Store.domain == self._normalize_domain(domain)))
            return store.id if store else None

    def upsert_store_and_get_id(
        self,
        domain_or_url: str,
        *,
        shop_name: str | None = None,
        currency_code: str | None = None,
        raw_metadata: dict[str, Any] | None = None,
    ) -> uuid.UUID:
        """Upsert store and return just the ID to avoid detached instance issues"""
        with get_session(self.session_factory) as session:
            store = self._upsert_store_in_session(
                session,
                domain_or_url=domain_or_url,
                shop_name=shop_name,
                currency_code=currency_code,
                raw_metadata=raw_metadata,
            )
            session.flush()
            store_id = store.id
            return store_id

    def upsert_store(
        self,
        domain_or_url: str,
        *,
        shop_name: str | None = None,
        currency_code: str | None = None,
        raw_metadata: dict[str, Any] | None = None,
    ) -> Store:
        with get_session(self.session_factory) as session:
            store = self._upsert_store_in_session(
                session,
                domain_or_url=domain_or_url,
                shop_name=shop_name,
                currency_code=currency_code,
                raw_metadata=raw_metadata,
            )
            session.flush()
            session.refresh(store)
            return store

    def upsert_product_from_shopify(self, store_url: str, payload: dict[str, Any]) -> Product:
        with get_session(self.session_factory) as session:
            store = self._upsert_store_in_session(session, domain_or_url=store_url)
            product = self._upsert_product_in_session(session, store=store, payload=payload)
            store.last_synced_at = datetime.now().astimezone()
            session.flush()
            session.refresh(product)
            return product

    def _upsert_store_in_session(
        self,
        session: Session,
        *,
        domain_or_url: str,
        shop_name: str | None = None,
        currency_code: str | None = None,
        raw_metadata: dict[str, Any] | None = None,
    ) -> Store:
        domain = self._normalize_domain(domain_or_url)
        base_url = self._normalize_base_url(domain_or_url)
        store = session.scalar(select(Store).where(Store.domain == domain))

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

    def _upsert_product_in_session(self, session: Session, *, store: Store, payload: dict[str, Any]) -> Product:
        shopify_product_id = int(payload["id"])
        product = session.scalar(
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

        session.flush()

        self._replace_options(session, product, payload.get("options", []))
        image_map = self._replace_images(session, product, payload.get("images", []))
        self._replace_variants(session, product, payload.get("variants", []), image_map=image_map)

        return product

    def _replace_options(self, session: Session, product: Product, options: list[dict[str, Any]]) -> None:
        session.execute(delete(ProductOptionValue).where(ProductOptionValue.option_id.in_(select(ProductOption.id).where(ProductOption.product_id == product.id))))
        session.execute(delete(ProductOption).where(ProductOption.product_id == product.id))

        for option_payload in options:
            option = ProductOption(
                product=product,
                name=option_payload.get("name") or "Option",
                position=option_payload.get("position"),
            )
            session.add(option)
            session.flush()
            for index, value in enumerate(option_payload.get("values", []), start=1):
                session.add(ProductOptionValue(option=option, value=str(value), position=index))

    def _replace_images(
        self, session: Session, product: Product, images: list[dict[str, Any]]
    ) -> dict[int, ProductImage]:
        session.execute(delete(VariantImageLink).where(VariantImageLink.image_id.in_(select(ProductImage.id).where(ProductImage.product_id == product.id))))
        session.execute(delete(ProductImage).where(ProductImage.product_id == product.id))

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
            session.flush()
            image_map[image.shopify_image_id] = image
        return image_map

    def _replace_variants(
        self,
        session: Session,
        product: Product,
        variants: list[dict[str, Any]],
        *,
        image_map: dict[int, ProductImage],
    ) -> None:
        session.execute(delete(VariantImageLink).where(VariantImageLink.variant_id.in_(select(ProductVariant.id).where(ProductVariant.product_id == product.id))))
        session.execute(delete(ProductVariant).where(ProductVariant.product_id == product.id))

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
            session.flush()

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