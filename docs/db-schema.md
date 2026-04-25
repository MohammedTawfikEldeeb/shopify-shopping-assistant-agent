# Database Schema

This schema is designed for Shopify `/products.json` ingestion into Postgres.

## Core tables

- `stores`: one row per Shopify domain such as `ystudios.net`
- `products`: canonical product records scoped to a store
- `product_variants`: purchasable variants such as `M / White`
- `product_images`: product image assets
- `variant_image_links`: many-to-many link between variants and images
- `product_options`: option groups such as `Size` and `Color`
- `product_option_values`: option values such as `S`, `M`, `White`

Recommended usage:

1. Fetch `https://store-domain/products.json`
2. Upsert the store and each product payload into Postgres

## Why this shape works well

- Shopify ids are preserved in dedicated columns, so re-syncs stay idempotent.
- Raw payload JSON is retained on products, variants, and images, so you can re-parse later without re-fetching.
- Product metadata is normalized enough for analytics and filtering, but not so fragmented that ingestion becomes painful.
