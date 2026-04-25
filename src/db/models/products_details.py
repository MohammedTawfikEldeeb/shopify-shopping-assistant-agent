from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from ..base import Base


class SyncStatus(StrEnum):
    PENDING = "pending"
    SYNCED = "synced"
    FAILED = "failed"


class Store(Base):
    __tablename__ = "stores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    domain: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    base_url: Mapped[str] = mapped_column(String(512))
    shop_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    currency_code: Mapped[str | None] = mapped_column(String(16), nullable=True)
    raw_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    products: Mapped[list["Product"]] = relationship(back_populates="store", cascade="all, delete-orphan")


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("store_id", "shopify_product_id", name="uq_products_store_shopify_product_id"),
        Index("ix_products_store_handle", "store_id", "handle"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), index=True)
    shopify_product_id: Mapped[int] = mapped_column(BigInteger)
    handle: Mapped[str] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(512))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    vendor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    product_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    shopify_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    shopify_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sync_status: Mapped[str] = mapped_column(String(32), default=SyncStatus.PENDING, nullable=False)
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    store: Mapped["Store"] = relationship(back_populates="products")
    variants: Mapped[list["ProductVariant"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )
    images: Mapped[list["ProductImage"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )
    options: Mapped[list["ProductOption"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )


class ProductVariant(Base):
    __tablename__ = "product_variants"
    __table_args__ = (
        UniqueConstraint("product_id", "shopify_variant_id", name="uq_variants_product_shopify_variant_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    shopify_variant_id: Mapped[int] = mapped_column(BigInteger)
    title: Mapped[str] = mapped_column(String(255))
    sku: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    option1: Mapped[str | None] = mapped_column(String(255), nullable=True)
    option2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    option3: Mapped[str | None] = mapped_column(String(255), nullable=True)
    available: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    compare_at_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    requires_shipping: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    taxable: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    grams: Mapped[int | None] = mapped_column(Integer, nullable=True)
    position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    shopify_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    shopify_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    product: Mapped["Product"] = relationship(back_populates="variants")
    image_links: Mapped[list["VariantImageLink"]] = relationship(back_populates="variant", cascade="all, delete-orphan")


class ProductImage(Base):
    __tablename__ = "product_images"
    __table_args__ = (
        UniqueConstraint("product_id", "shopify_image_id", name="uq_images_product_shopify_image_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    shopify_image_id: Mapped[int] = mapped_column(BigInteger)
    src: Mapped[str] = mapped_column(String(1024))
    alt_text: Mapped[str | None] = mapped_column(String(512), nullable=True)
    position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    shopify_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    shopify_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    product: Mapped["Product"] = relationship(back_populates="images")
    variant_links: Mapped[list["VariantImageLink"]] = relationship(
        back_populates="image", cascade="all, delete-orphan"
    )


class VariantImageLink(Base):
    __tablename__ = "variant_image_links"
    __table_args__ = (
        UniqueConstraint("variant_id", "image_id", name="uq_variant_image_links_variant_id_image_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    variant_id: Mapped[int] = mapped_column(ForeignKey("product_variants.id", ondelete="CASCADE"), index=True)
    image_id: Mapped[int] = mapped_column(ForeignKey("product_images.id", ondelete="CASCADE"), index=True)

    variant: Mapped["ProductVariant"] = relationship(back_populates="image_links")
    image: Mapped["ProductImage"] = relationship(back_populates="variant_links")


class ProductOption(Base):
    __tablename__ = "product_options"
    __table_args__ = (
        UniqueConstraint("product_id", "name", name="uq_product_options_product_id_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    position: Mapped[int | None] = mapped_column(Integer, nullable=True)

    product: Mapped["Product"] = relationship(back_populates="options")
    values: Mapped[list["ProductOptionValue"]] = relationship(
        back_populates="option", cascade="all, delete-orphan"
    )


class ProductOptionValue(Base):
    __tablename__ = "product_option_values"
    __table_args__ = (
        UniqueConstraint("option_id", "value", name="uq_product_option_values_option_id_value"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    option_id: Mapped[int] = mapped_column(ForeignKey("product_options.id", ondelete="CASCADE"), index=True)
    value: Mapped[str] = mapped_column(String(255))
    position: Mapped[int | None] = mapped_column(Integer, nullable=True)

    option: Mapped["ProductOption"] = relationship(back_populates="values")
