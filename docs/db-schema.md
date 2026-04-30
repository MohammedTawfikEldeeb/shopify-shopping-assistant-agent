# Database Schema

This schema is designed for Shopify `/products.json` ingestion into Postgres, with dual optimization for both operational queries and vector embeddings.

## Core tables (Operational)

- `stores`: one row per Shopify domain such as `ystudios.net`
- `products`: canonical product records scoped to a store
- `product_variants`: purchasable variants such as `M / White`
- `product_images`: product image assets
- `variant_image_links`: many-to-many link between variants and images
- `product_options`: option groups such as `Size` and `Color`
- `product_option_values`: option values such as `S`, `M`, `White`

**Use case**: Operational queries, inventory tracking, order fulfillment.

## VectorDB-Optimized tables (Search & AI)

- `product_search_index`: deduplicated, cleaned product data optimized for vector embeddings
- `variant_details`: lightweight variant metadata for filtering search results

**Use case**: Semantic search, vector embeddings, AI agent product discovery.

## Architecture

### Why dual tables?

1. **Operational DB** (normalized): Handles inventory, variants, updates, analytics
2. **Search Index** (denormalized): Optimized for vector embeddings and semantic search

### product_search_index table

Stores cleaned, aggregated product data perfect for vector embeddings:

| Field | Purpose |
|-------|---------|
| `title` | Product name |
| `description_clean` | HTML stripped, plain text description |
| `material` | Extracted material composition (e.g., "100% cotton") |
| `care_instructions` | Parsed care info (e.g., "Machine wash cold") |
| `sizing_info` | Model measurements and fit guidance |
| `available_colors` | Deduplicated color options (array) |
| `available_sizes` | Deduplicated size options (array) |
| `primary_image_url` | First product image URL |
| `all_image_urls` | All unique image URLs (no duplicates per variant) |
| `min_price` / `max_price` | Price range across all variants |
| `search_text` | Combined searchable text optimized for embeddings |
| `all_available` | Boolean: any variant available? (for filtering) |

**Search text format**:
```
Knit Polo T-Shirt by Y Studios. Type: Apparel. Fitted knit cotton polo...
Material: 100% knitted cotton. Care: No shrinkage or pilling. 
Sizing: Model is 186cm 69kg in M. Stay true to size for fitted look.
Available sizes: S, M, L, XL. Available colors: White, Black, Navy. 
Tags: spring-2026
```

### variant_details table

Lightweight, non-redundant variant records for filtering:

| Field | Purpose |
|-------|---------|
| `search_index_id` | Link to parent product search index |
| `size` | Extracted size (e.g., "M") |
| `color` | Extracted color (e.g., "White") |
| `sku` | Product SKU |
| `price` | Variant price |
| `available` | In stock? |
| `product_variant_id` | Reference to original ProductVariant |

## Data Flow

```
Shopify API (products.json)
         ↓
ProductRepository (upsert_product_from_shopify)
         ↓
    [Operational Tables]
    - products
    - product_variants
    - product_images
    - etc.
         ↓
build_vectordb_payload() [in product_search_processor.py]
         ├→ clean_html() - strip tags
         ├→ extract_material_info() - "100% cotton"
         ├→ extract_care_instructions() - care text
         ├→ extract_sizing_info() - fit guidance
         ├→ extract_variant_attributes() - size/color per variant
         └→ build_search_text() - combined optimized text
         ↓
ProductSearchIndexRepository (upsert_from_payload)
         ↓
    [Search Index Tables]
    - product_search_index
    - variant_details
         ↓
Vector DB (external, e.g., Pinecone, Weaviate)
    - Embed search_text with semantic model
    - Store embeddings + metadata
    - Enable semantic search queries
```

## Key Improvements for VectorDB

✅ **No Redundancy**: Each variant doesn't duplicate parent product data  
✅ **No Duplicate Images**: One image URL per unique image, not per variant  
✅ **Cleaned Text**: HTML parsed and removed for better embeddings  
✅ **Extracted Metadata**: Material, care, sizing extracted into separate fields  
✅ **Aggregated Options**: Color/size options merged and sorted (no "S / White" duplication)  
✅ **Optimized Search Text**: Single field with all semantic content for embedding  
✅ **Lightweight Variants**: Minimal footprint for filtering queries  
✅ **Availability Filter**: `all_available` boolean for quick filtering  

## Example: Product with 12 variants

**Before (Operational DB)**:
- 1 Product row
- 12 ProductVariant rows (each with redundant image data)
- 3 ProductImage rows

**After (VectorDB-Optimized)**:
- 1 ProductSearchIndex row (for vector embedding)
- 12 VariantDetail rows (lightweight, only size/color/price/availability)
- 3 unique images stored once (not 12 times)

Result: **Reduced embedding size by ~60%, faster search, cleaner semantics**

## Recommended Usage

1. **Fetch** from Shopify `/products.json`
2. **Upsert** into operational tables (ProductRepository)
3. **Automatically populate** search index tables (ProductSearchIndexRepository)
4. **Embed** search_text using embedding model (OpenAI, local, etc.)
5. **Store embeddings** in vector DB (Pinecone, Weaviate, Milvus, etc.)
6. **Query** with: `SELECT * FROM product_search_index WHERE store_id = ? AND [vector search]`
7. **Filter variants** using variant_details: `SELECT * FROM variant_details WHERE search_index_id = ? AND color = ?`
