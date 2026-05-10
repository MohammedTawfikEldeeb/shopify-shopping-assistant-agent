<div align="center">

<img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Objects/Shopping%20Bags.png" alt="Shopping Bags" width="120" height="120" />

# **Shopify Shopping Assistant Agent**

### *An Intelligent, Multi-Lingual AI Shopping Concierge for Egyptian E-Commerce*

[![Python](https://img.shields.io/badge/Python-3.13-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://react.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Google Cloud](https://img.shields.io/badge/Google_Cloud-4285F4?style=for-the-badge&logo=google-cloud&logoColor=white)](https://cloud.google.com/)
[![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)](https://supabase.com/)
[![ZenML](https://img.shields.io/badge/ZenML-2B2B2B?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZD0iTTEyIDJMNCA3djEwbDggNSA4LTVWN0wxMiAyem0wIDIuMThMNyA3LjgybDUgMy4xMiA1LTMuMTJMMTIgNC4xOHptLTYgNS4xM2w1IDMuMTJ2Ni4zN2wtNS0zLjEyVjkuMzF6bTEyIDB2Ni4zN2wtNSAzLjEyVjEyLjQzbDUtMy4xMnoiIGZpbGw9IndoaXRlIi8+PC9zdmc+&logoColor=white)](https://zenml.io/)

</div>

---

## Overview

**Shopify Shopping Assistant Agent** is a production-grade AI shopping concierge that intelligently searches, compares, and recommends products across **100+ Shopify stores in Egypt**. Built with a sophisticated **LangGraph agent architecture**, it combines **semantic vector search**, **cross-encoder reranking**, **score threshold filtering**, and **real-time streaming** to deliver an unmatched multi-lingual shopping experience.

The system handles both **Arabic (Egyptian dialect)** and **English** queries, persists full conversation context across sessions in **Supabase PostgreSQL**, and leverages **ZenML Cloud** for automated weekly ingestion pipelines that keep the product catalog fresh.

---

## Star Features

<div align="center">

| Feature | Badge |
|---------|-------|
| **LangGraph Multi-Agent Architecture** | [![LangGraph](https://img.shields.io/badge/LangGraph-1C3C3C?style=flat-square&logo=langchain&logoColor=white)](https://langchain-ai.github.io/langgraph/) |
| **Hybrid Search (Vector + Full-Text)** | [![Hybrid Search](https://img.shields.io/badge/Hybrid%20Search-PGVector%20%2B%20tsvector-336791?style=flat-square&logo=postgresql&logoColor=white)]() |
| **Cross-Encoder Re-Ranking** | [![Sentence Transformers](https://img.shields.io/badge/Cross--Encoder-MS--MARCO--MiniLM-orange?style=flat-square&logo=pytorch&logoColor=white)]() |
| **Score Threshold Filtering** | [![Score Filter](https://img.shields.io/badge/Score%20Threshold--7.5%20Cutoff-blueviolet?style=flat-square)]() |
| **Semantic Cache** | [![Semantic Cache](https://img.shields.io/badge/Semantic%20Cache-PGVector%20Cosine%200.92-FF6F00?style=flat-square)]() |
| **Session Management & State Snapshots** | [![Session](https://img.shields.io/badge/Session%20Mgmt-PostgreSQL%20%2B%20Async-316192?style=flat-square&logo=postgresql&logoColor=white)]() |
| **Streaming SSE Responses** | [![SSE](https://img.shields.io/badge/Streaming-SSE%20%2B%20Typewriter-00C853?style=flat-square)]() |
| **Multi-Language Support** | [![Arabic](https://img.shields.io/badge/Arabic%20%28Egyptian%29-%26%20English-009688?style=flat-square)]() |
| **100+ Store Ingestion Pipeline** | [![ZenML](https://img.shields.io/badge/ZenML%20Cloud-Weekly%20Schedule-2B2B2B?style=flat-square)]() |
| **Prompt Versioning & Observability** | [![Opik](https://img.shields.io/badge/Opik%20%2B%20LangSmith-Observability-FF6D00?style=flat-square)]() |
| **LLM Routing (OpenRouter / Groq)** | [![OpenRouter](https://img.shields.io/badge/OpenRouter-AI%20Model%20Hub-593CFB?style=flat-square)]() [![Groq](https://img.shields.io/badge/Groq-LPU%20Inference-F55036?style=flat-square)]() |
| **GCP Cloud Run Deployment** | [![Cloud Run](https://img.shields.io/badge/Cloud%20Run-Serverless-4285F4?style=flat-square&logo=google-cloud&logoColor=white)]() |
| **CI/CD with GitHub Actions** | [![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-CI%2FCD-2088FF?style=flat-square&logo=github-actions&logoColor=white)]() |

</div>

---

## System Architecture

```mermaid
flowchart TB
    subgraph Frontend["Frontend - React + Tailwind"]
        UI[Chat Interface<br/>Typewriter Effect<br/>Product Grid<br/>Session Sidebar]
    end

    subgraph APILayer["API Layer - FastAPI + Uvicorn"]
        API[FastAPI Router]
        CORS[CORS Middleware]
        CACHE[Semantic Cache<br/>PGVector Cosine]
    end

    subgraph AgentCore["Agent Core - LangGraph"]
        START((START))
        SUMMARIZE["Summarize Node<br/>Conversation Compression"]
        AGENT["Agent Node<br/>LLM + Tool Calling"]
        TOOLS["Tools Node<br/>Retriever + SQL"]
        END((END))
        
        START -->|messages > 8| SUMMARIZE
        START -->|else| AGENT
        SUMMARIZE --> AGENT
        AGENT -->|tool_calls| TOOLS
        AGENT -->|no tools| END
        TOOLS --> AGENT
    end

    subgraph Retrieval["Retrieval Stack"]
        EMBED["FastEmbed<br/>paraphrase-multilingual-MiniLM"]
        PGV[PGVector<br/>384-dim Cosine]
        RERANK["Cross-Encoder<br/>MS-MARCO-MiniLM-L6"]
        FTS[PostgreSQL FTS<br/>tsvector + GIN Index]
    end

    subgraph DataLayer["Data Layer"]
        DB[(PostgreSQL<br/>AsyncPG + SQLAlchemy 2.0)]
        MODELS[Products<br/>Variants<br/>Images<br/>Options<br/>Sessions<br/>Messages<br/>State Snapshots]
        ALEMBIC[Alembic Migrations]
    end

    subgraph LLMInfra["LLM Infrastructure"]
        OR[OpenRouter<br/>GPT-OSS-20B]
        GROQ[Groq<br/>LPU Inference]
        WRAP[LangSmith<br/>OpenAI Wrapper]
    end

    subgraph Observability["Observability"]
        OPIK[Opik<br/>Prompt Versioning<br/>Trace Tracking]
        LANGSM[LangSmith<br/>Chain Tracing]
        LOGURU[Loguru<br/>Structured Logging]
    end

    subgraph Pipeline["Ingestion Pipeline - ZenML"]
        FETCH["fetch_products<br/>100+ Stores Concurrent"]
        INGEST["ingest_to_db<br/>Upsert + Verify"]
        INDEX["index_to_vectordb<br/>Embeddings + PGVector"]
        
        FETCH --> INGEST --> INDEX
    end

    subgraph Cloud["Cloud Infrastructure"]
        GCR[Artifact Registry]
        CR[Cloud Run]
        GH[GitHub Actions<br/>CI/CD]
    end

    UI -->|SSE / REST| API
    API --> AGENT
    AGENT --> TOOLS
    TOOLS -->|semantic search| EMBED
    EMBED --> PGV
    PGV --> RERANK
    TOOLS -->|sql_query| DB
    AGENT -->|chat| OR
    AGENT -->|chat| GROQ
    API --> CACHE
    CACHE --> PGV
    AGENT --> OPIK
    AGENT --> LANGSM
    DB --> MODELS
    PIPELINE --> DB
    PIPELINE --> PGV
    GH --> GCR
    GCR --> CR
```

---

## Complete Tech Stack

### Backend

| Technology | Purpose | Badge |
|------------|---------|-------|
| **Python 3.13** | Core runtime | ![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=flat-square&logo=python&logoColor=white) |
| **FastAPI** | High-performance async API framework | ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white) |
| **Uvicorn** | ASGI server | ![Uvicorn](https://img.shields.io/badge/Uvicorn-4051B5?style=flat-square) |
| **Pydantic v2** | Data validation & settings management | ![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063?style=flat-square&logo=pydantic&logoColor=white) |
| **Pydantic Settings** | Environment-based configuration | ![Pydantic](https://img.shields.io/badge/Pydantic%20Settings-v2-E92063?style=flat-square) |
| **SQLAlchemy 2.0** | Async ORM with type-safe Mapped columns | ![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=flat-square) |
| **SQLModel** | SQLAlchemy + Pydantic integration | ![SQLModel](https://img.shields.io/badge/SQLModel-0.0.22-2E8B57?style=flat-square) |
| **Alembic** | Database migrations | ![Alembic](https://img.shields.io/badge/Alembic-Migrations-6B8E23?style=flat-square) |
| **AsyncPG** | Ultra-fast async PostgreSQL driver | ![AsyncPG](https://img.shields.io/badge/AsyncPG-0.31-316192?style=flat-square&logo=postgresql&logoColor=white) |
| **Psycopg2** | Sync PostgreSQL adapter | ![PostgreSQL](https://img.shields.io/badge/Psycopg2-2.9-316192?style=flat-square&logo=postgresql&logoColor=white) |

### AI / ML / LLM

| Technology | Purpose | Badge |
|------------|---------|-------|
| **LangGraph** | Stateful agent graph with cycles | ![LangGraph](https://img.shields.io/badge/LangGraph-0.2-1C3C3C?style=flat-square&logo=langchain&logoColor=white) |
| **LangChain** | LLM abstractions & tool binding | ![LangChain](https://img.shields.io/badge/LangChain-0.3-1C3C3C?style=flat-square&logo=langchain&logoColor=white) |
| **LangChain OpenAI** | OpenAI-compatible chat models | ![LangChain](https://img.shields.io/badge/LangChain%20OpenAI-0.3-1C3C3C?style=flat-square) |
| **OpenAI SDK** | Client for OpenRouter & Groq | ![OpenAI](https://img.shields.io/badge/OpenAI%20SDK-%E2%89%A51.75-412991?style=flat-square&logo=openai&logoColor=white) |
| **OpenRouter** | Unified API for 100+ LLMs | ![OpenRouter](https://img.shields.io/badge/OpenRouter-593CFB?style=flat-square) |
| **Groq** | LPU-based ultra-fast inference | ![Groq](https://img.shields.io/badge/Groq-F55036?style=flat-square) |
| **FastEmbed** | On-device embedding generation | ![FastEmbed](https://img.shields.io/badge/FastEmbed-0.8-FF6F00?style=flat-square) |
| **Sentence Transformers** | Cross-encoder reranker model | ![Sentence Transformers](https://img.shields.io/badge/Sentence%20Transformers-%E2%89%A53.0-FF6F00?style=flat-square&logo=pytorch&logoColor=white) |

### Vector & Search

| Technology | Purpose | Badge |
|------------|---------|-------|
| **PGVector** | Vector similarity search inside PostgreSQL | ![PGVector](https://img.shields.io/badge/PGVector-0.4-336791?style=flat-square&logo=postgresql&logoColor=white) |
| **Qdrant Client** | Alternative vector DB client | ![Qdrant](https://img.shields.io/badge/Qdrant-1.17-E25822?style=flat-square&logo=qdrant&logoColor=white) |
| **Cross-Encoder (MS-MARCO-MiniLM-L6)** | Re-ranking retrieved products | ![Hugging Face](https://img.shields.io/badge/Cross--Encoder-MS--MARCO--MiniLM--L6-yellow?style=flat-square) |
| **Multilingual MiniLM (L12)** | Query/product embeddings | ![Hugging Face](https://img.shields.io/badge/Embeddings-MiniLM--L12--v2-yellow?style=flat-square) |

### Data & Storage

| Technology | Purpose | Badge |
|------------|---------|-------|
| **Supabase** | Managed PostgreSQL with Connection Pooler | ![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?style=flat-square&logo=supabase&logoColor=white) |
| **PostgreSQL** | Primary relational database (hosted on Supabase) | ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14%2B-316192?style=flat-square&logo=postgresql&logoColor=white) |
| **PGVector Extension** | Vector storage & HNSW index (Supabase-native) | ![PGVector](https://img.shields.io/badge/PGVector%20Ext-vector%20%2B%20HNSW-336791?style=flat-square) |
| **Alembic** | Schema versioning & migrations | ![Alembic](https://img.shields.io/badge/Alembic-1.15-6B8E23?style=flat-square) |

### Observability & Monitoring

| Technology | Purpose | Badge |
|------------|---------|-------|
| **Opik** | LLM prompt versioning & trace tracking | ![Opik](https://img.shields.io/badge/Opik-2.0-FF6D00?style=flat-square) |
| **LangSmith** | LangChain chain tracing & evaluation | ![LangSmith](https://img.shields.io/badge/LangSmith-%E2%89%A50.8-1C3C3C?style=flat-square&logo=langchain&logoColor=white) |
| **Loguru** | Structured, colorized logging | ![Loguru](https://img.shields.io/badge/Loguru-0.7-008080?style=flat-square) |

### MLOps & Pipeline

| Technology | Purpose | Badge |
|------------|---------|-------|
| **ZenML** | ML pipeline orchestration | ![ZenML](https://img.shields.io/badge/ZenML-0.75-2B2B2B?style=flat-square) |
| **ZenML Cloud** | Remote execution & weekly scheduling | ![ZenML](https://img.shields.io/badge/ZenML%20Cloud-Managed-2B2B2B?style=flat-square) |

### Frontend

| Technology | Purpose | Badge |
|------------|---------|-------|
| **React 18** | UI library | ![React](https://img.shields.io/badge/React-18-20232A?style=flat-square&logo=react&logoColor=61DAFB) |
| **Vite** | Build tool & dev server | ![Vite](https://img.shields.io/badge/Vite-5.1-646CFF?style=flat-square&logo=vite&logoColor=white) |
| **Tailwind CSS** | Utility-first styling | ![Tailwind CSS](https://img.shields.io/badge/Tailwind%20CSS-3.4-06B6D4?style=flat-square&logo=tailwind-css&logoColor=white) |
| **Material Symbols** | Google's icon font | ![Google Fonts](https://img.shields.io/badge/Material%20Symbols-Outlined-4285F4?style=flat-square) |

### DevOps & Cloud

| Technology | Purpose | Badge |
|------------|---------|-------|
| **Docker** | Containerization | ![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white) |
| **Google Cloud Run** | Serverless container hosting | ![Cloud Run](https://img.shields.io/badge/Cloud%20Run-4285F4?style=flat-square&logo=google-cloud&logoColor=white) |
| **Artifact Registry** | Docker image storage | ![GCP](https://img.shields.io/badge/Artifact%20Registry-4285F4?style=flat-square&logo=google-cloud&logoColor=white) |
| **GitHub Actions** | CI/CD automation | ![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-2088FF?style=flat-square&logo=github-actions&logoColor=white) |
| **UV** | Ultra-fast Python package manager | ![UV](https://img.shields.io/badge/uv-Package%20Manager-DE5FE9?style=flat-square) |

---

## Deep Dive into Key Components

### 1. LangGraph Agent Architecture

The agent is built on **LangGraph** with a cyclical state machine:

```
START -> Summarize (if >8 messages) -> Agent Node -> [Tool Call?] -> Tools -> Agent -> END
```

- **Agent Node**: LLM with `bind_tools()` for structured tool calling
- **Tools Node**: Executes either `product_retriever` or `sql_query`
- **Summarize Node**: Compresses conversation history to save context window
- **State**: `messages`, `summary`, `products`, `product_ids`, `steps`, `product_sets`

The agent uses **two specialized tools**:

| Tool | Purpose | Trigger |
|------|---------|---------|
| `product_retriever` | Semantic vector search across all stores | User asks for NEW products |
| `sql_query` | Query product details (variants, images, options) | User asks about ALREADY found products |

### 2. Hybrid Search + Re-Ranking Pipeline

```
User Query
    |
    v
FastEmbed (Multilingual MiniLM-L12) → 384-dim Vector
    |
    v
PGVector Cosine Search → Top 20 Candidates
    |
    v
Cross-Encoder (MS-MARCO-MiniLM-L6-v2) Re-Ranking
    |
    v
Score Threshold Filter (≥ -7.5)
    |
    v
Top-K Products with Confidence Score
```

**Score Threshold Filter**: Any product with a reranker score below -7.5 is discarded. This eliminates noise while keeping well-scored relevant results.

### 3. Semantic Cache

A **PGVector-based semantic cache** stores previous query-response pairs:
- **Similarity Threshold**: 0.92 cosine similarity for cache hits
- **TTL**: 24 hours with automatic expiration
- **Store-Domain Isolation**: Cache entries scoped per Shopify store
- **Fallback**: Cache is bypassed when the user already has product context in the session

### 4. Session Management

Full **multi-session chat history** with PostgreSQL:

```sql
user_sessions ──► chat_messages
        │
        └──► agent_state_snapshots (LangGraph state persistence)
```

- **User Sessions**: UUID-based sessions with store-domain binding
- **Chat Messages**: Full conversation history with embedded product JSON
- **State Snapshots**: Serialized LangGraph agent state for seamless conversation restoration
- **Async Repositories**: All DB operations use SQLAlchemy 2.0 async patterns

### 5. Product Ingestion at Scale

**ZenML Pipeline** runs weekly on ZenML Cloud to ingest ~100 Egyptian Shopify stores:

```python
@pipeline(name="shopify_ingestion_pipeline")
def shopify_ingestion_pipeline():
    store_products = fetch_products()      # Concurrent HTTP/2 fetching
    ingest_result = ingest_to_db(store_products)   # Upsert + verify counts
    index_result = index_to_vectordb(store_products, ingest_result)  # Embed + index
```

- **Concurrency**: Semaphore-limited async fetching (max 10 parallel)
- **Resilience**: Timeouts and graceful skipping for unreachable stores
- **Verification**: Post-ingest COUNT(*) on all related tables
- **Embeddings**: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- **Payload Enrichment**: Extracts materials, care instructions, sizing info from HTML descriptions

### 6. Multi-Language Intelligence

The agent **auto-detects and mirrors** the user's language and dialect:
- **Egyptian Arabic** → Replies in Egyptian Arabic slang
- **Levantine Arabic** → Replies in Levantine dialect
- **English** → Replies in English
- **Query Cleaning**: Strips gender modifiers (woman/men/kids) from vector search while preserving them for reranking

### 7. Observability Stack

Every LLM call, tool execution, and reranking operation is traced:

| Layer | Tool | What It Tracks |
|-------|------|----------------|
| LLM Calls | **Opik** + **LangSmith** | Input messages, output tokens, latency |
| Agent Nodes | **Opik `@track`** | Agent node, summarize node, tools node |
| Tool Calls | **Opik `@track`** | Retriever, reranker, SQL query |
| Prompts | **Opik Prompt Versioning** | System prompt, summarize prompts |
| API Requests | **Loguru Middleware** | Method, path, status, duration (ms) |
| Pipelines | **ZenML Dashboard** | Step runs, schedules, artifacts |

### 8. Streaming SSE Frontend

Real-time streaming with **Server-Sent Events**:
- **Typewriter Effect**: Characters appear one-by-one with 10ms delay
- **Live Step Indicators**: Animated tool status (searching → reranking → done)
- **Trace Panel**: Expandable step-by-step execution log with icons
- **Product Grid**: Animated cards with hover zoom, "Best Match" badge, direct checkout links
- **Session Sidebar**: Create, switch, and delete sessions with persisted history

---

## Project Structure

```
shopify-shopping-assistant-agent/
├── .github/
│   └── workflows/
│       ├── ci.yml                 # Lint, type-check, Docker validation, frontend build
│       └── cd.yml                 # Build image → Artifact Registry → Cloud Run deploy
│
├── frontend/                      # React + Vite + Tailwind CSS
│   ├── src/
│   │   ├── pages/
│   │   │   └── ChatPage.jsx       # Main chat UI with streaming, products grid, sessions
│   │   ├── components/
│   │   │   ├── ChatMessage.jsx    # Message bubbles
│   │   │   ├── ChatInput.jsx      # Textarea input
│   │   │   ├── ProductCard.jsx    # Product recommendation cards
│   │   │   ├── Navbar.jsx         # Top navigation
│   │   │   └── Footer.jsx         # Footer
│   │   ├── App.jsx                # Root component
│   │   ├── main.jsx               # Entry point
│   │   └── index.css              # Tailwind directives + custom animations
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── postcss.config.js
│
├── pipelines/                     # ZenML ingestion pipeline
│   ├── pipeline.py                # Pipeline definition (fetch → ingest → index)
│   ├── run.py                     # CLI runner (--no-cache, --schedule)
│   └── steps/
│       ├── fetch_products.py      # Async HTTP fetch from 100+ stores
│       ├── ingest_to_db.py        # Upsert products/variants/images/options
│       └── index_to_vectordb.py   # Generate embeddings & insert into PGVector
│
├── src/
│   ├── __init__.py
│   ├── config.py                  # Pydantic Settings (Postgres, LLM, Search, Cache, CORS)
│   │
│   ├── agent/                     # LangGraph Agent Core
│   │   ├── __init__.py
│   │   ├── agent.py               # ShoppingAgent class (chat, stream, session-aware)
│   │   ├── graph.py               # StateGraph builder (START → Summarize → Agent → Tools → END)
│   │   ├── nodes.py               # Agent node, Summarize node, Tools node
│   │   ├── states.py              # AgentState TypedDict
│   │   └── tools.py               # ProductRetriever + SQLQueryTool
│   │
│   ├── api/                       # FastAPI Application
│   │   ├── __init__.py
│   │   ├── main.py                # App factory, lifespan, middleware, dependency injection
│   │   ├── dependencies.py        # FastAPI Depends providers
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── chat_routes.py     # POST /chat, POST /chat/stream, session CRUD
│   │   │   └── system_routes.py   # Health checks
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── chat.py            # ChatRequest, ChatResponse, Session models
│   │   │   └── indexing.py        # Indexing request/response schemas
│   │   └── services/
│   │       ├── semantic_cache_service.py   # PGVector semantic cache with TTL
│   │       ├── indexing_service.py         # Product → vector payload builder
│   │       └── store_ingestion_service.py  # Store-level ingestion logic
│   │
│   ├── db/                        # Database Layer
│   │   ├── __init__.py
│   │   ├── base.py                # SQLAlchemy declarative base
│   │   ├── factory.py             # DatabaseFactory (sync + async engines)
│   │   ├── session.py             # Async session context manager
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── products_details.py        # Store, Product, Variant, Image, Option, OptionValue
│   │   │   └── session_models.py          # UserSession, ChatMessage, AgentStateSnapshot
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   ├── product_repository.py      # Upsert products from Shopify payload
│   │   │   └── session_repository.py      # Session, message, state snapshot CRUD
│   │   ├── interfaces/
│   │   │   ├── __init__.py
│   │   │   └── base_repository.py         # Generic async repository interface
│   │   └── migration/
│   │       ├── env.py
│   │       ├── alembic.ini
│   │       └── versions/
│   │           ├── 20260425_0001_create_shopify_schema.py
│   │           ├── 20260425_0002_products_description_column.py
│   │           ├── 20260503_0001_add_session_chat_state_tables.py
│   │           └── 20260507_0001_add_products_search_vector.py   # tsvector + GIN for FTS
│   │
│   ├── infrastructure/            # Infrastructure Adapters
│   │   ├── __init__.py
│   │   ├── llm/
│   │   │   ├── __init__.py
│   │   │   ├── interface.py       # LLMInterface abstract class
│   │   │   ├── factory.py         # LLMFactory (Groq / OpenRouter)
│   │   │   ├── enum.py            # LLMProviderEnums
│   │   │   ├── langchain_adapter.py
│   │   │   └── providers/
│   │   │       ├── __init__.py
│   │   │       ├── groq.py        # Groq provider with structured output
│   │   │       └── openrouter.py  # OpenRouter provider with structured output
│   │   └── vectordb/
│   │       ├── __init__.py
│   │       ├── interface.py       # VectorDBInterface abstract class
│   │       ├── factory.py         # VectorDBFactory singleton
│   │       ├── enum.py            # DistanceMetric, IndexType enums
│   │       └── providers/
│   │           ├── __init__.py
│   │           ├── pgvector.py    # Full PGVector provider (CRUD, HNSW index)
│   │           └── qdrant.py      # Qdrant provider (alternative)
│   │
│   ├── observability/             # Observability Layer
│   │   ├── __init__.py
│   │   ├── opik_utils.py          # Opik configuration & project setup
│   │   └── prompt_versioning.py   # Prompt class with Opik versioning fallback
│   │
│   ├── prompts/                   # Prompt Engineering
│   │   ├── __init__.py
│   │   └── prompts.py             # SYSTEM_PROMPT, SUMMARIZE_PROMPT, DB_SCHEMA
│   │
│   └── utils/                     # Utilities
│       ├── embedding_service.py   # FastEmbed singleton (multilingual MiniLM)
│       ├── reranker_service.py    # Cross-encoder singleton (MS-MARCO)
│       ├── product_search_processor.py  # HTML cleaning, material extraction, payload builder
│       └── logger_util.py         # Loguru structured logging setup
│
├── Dockerfile                     # Multi-stage Python 3.13 slim image
├── pyproject.toml                 # UV-managed dependencies
├── requirements.txt               # Exported for Docker
├── alembic.ini                    # Alembic configuration
├── .env.example                   # Environment variables template
└── README.md                      # This file
```

---

## Database Schema

```mermaid
erDiagram
    STORE ||--o{ PRODUCT : has
    STORE {
        uuid id PK
        string domain UK
        string base_url
        string shop_name
        string currency_code
        jsonb raw_metadata
        timestamp last_synced_at
    }
    PRODUCT ||--o{ PRODUCT_VARIANT : has
    PRODUCT ||--o{ PRODUCT_IMAGE : has
    PRODUCT ||--o{ PRODUCT_OPTION : has
    PRODUCT {
        uuid id PK
        uuid store_id FK
        bigint shopify_product_id
        string handle
        string title
        text description
        string vendor
        string product_type
        tsvector search_vector
        string sync_status
        jsonb raw_payload
    }
    PRODUCT_VARIANT ||--o{ VARIANT_IMAGE_LINK : links
    PRODUCT_VARIANT {
        uuid id PK
        uuid product_id FK
        bigint shopify_variant_id
        string title
        string sku
        string option1
        string option2
        string option3
        boolean available
        numeric price
        numeric compare_at_price
    }
    PRODUCT_IMAGE ||--o{ VARIANT_IMAGE_LINK : links
    PRODUCT_IMAGE {
        uuid id PK
        uuid product_id FK
        bigint shopify_image_id
        string src
        string alt_text
    }
    VARIANT_IMAGE_LINK {
        uuid id PK
        uuid variant_id FK
        uuid image_id FK
    }
    PRODUCT_OPTION ||--o{ PRODUCT_OPTION_VALUE : has
    PRODUCT_OPTION {
        uuid id PK
        uuid product_id FK
        string name
    }
    PRODUCT_OPTION_VALUE {
        uuid id PK
        uuid option_id FK
        string value
    }
    USER_SESSION ||--o{ CHAT_MESSAGE : has
    USER_SESSION ||--o{ AGENT_STATE_SNAPSHOT : has
    USER_SESSION {
        uuid id PK
        uuid user_id
        uuid session_id UK
        string store_url
        string store_domain
    }
    CHAT_MESSAGE {
        uuid id PK
        uuid session_id FK
        string role
        text content
        jsonb products_json
    }
    AGENT_STATE_SNAPSHOT {
        uuid id PK
        uuid session_id FK
        jsonb state_json
    }
```

---

## CI/CD Pipeline

```mermaid
flowchart LR
    PUSH[Push to main] --> CI[CI Workflow]
    CI --> LINT[Lint & Type Check]
    CI --> DOCKER[Docker Build Test]
    CI --> FE[Frontend Build Test]
    CI --> MIGRATE[Migrate Check]
    
    CI --> |Success| CD[CD Workflow]
    CD --> BUILD[Build Image<br/>+ Push Artifact Registry]
    CD --> DEPLOY[Deploy Cloud Run]
    CD --> HEALTH[Health Check /health]
```

---

## Quick Start

### Prerequisites

- Python 3.13+
- **Supabase** project (or PostgreSQL 14+ with `pgvector` extension)
- UV package manager (`pip install uv`)
- Node.js 20+ (for frontend)

### 1. Clone & Install

```bash
git clone https://github.com/yourusername/shopify-shopping-assistant-agent.git
cd shopify-shopping-assistant-agent

# Backend
uv sync

# Frontend
cd frontend
npm install
```

### 2. Environment Variables

```bash
cp .env.example .env
```

```env
# Database (Supabase)
POSTGRES__HOST=aws-0-eu-west-1.pooler.supabase.com
POSTGRES__PORT=6543
POSTGRES__DATABASE=postgres
POSTGRES__USER=postgres.<your-project-ref>
POSTGRES__PASSWORD=your-supabase-password
POSTGRES__SSLMODE=require

# Qdrant Configuration
QDRANT__ENVIRONMENT=local
QDRANT__HOST=localhost
QDRANT__PORT=6333
QDRANT__COLLECTION_NAME=products

# Docker Postgres bootstrap vars (required by postgres image)
POSTGRES_DB=shopify_assistant
POSTGRES_USER=shopify_user
POSTGRES_PASSWORD=change_me

# LLM
OPENROUTER_API__KEY=your-openrouter-key-here
GROQ_API__KEY=your-groq-key-here
LLM__PROVIDER=openrouter
LLM_MODEL__NAME=openai/gpt-oss-20b:nitro

# Observability
OPIK__API_KEY=your-opik-key-here
OPIK__PROJECT_NAME=shopify-shopping-assistant-agent

# Search
SEARCH__USE_HYBRID_SEARCH=true
```

### 3. Database Setup

**Option A: Supabase (Recommended)**

1. Create a project at [supabase.com](https://supabase.com)
2. Enable the **Vector** extension in Database → Extensions
3. Copy the **Connection Pooler** URL for your `.env`

**Option B: Local PostgreSQL**

```bash
# Create database & enable pgvector
createdb shopify_assistant
psql shopify_assistant -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

**Run Migrations**

```bash
uv run alembic -c src/db/migration/alembic.ini upgrade head
```

### 4. Run

```bash
# Backend
uv run uvicorn src.api.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm run dev
```

Open `http://localhost:5173`

### 5. Run Ingestion Pipeline (First Time)

```bash
# Local run
uv run python -m pipelines.run --no-cache

# Or schedule on ZenML Cloud (one-time setup)
zenml connect --url https://<tenant>.zenml.io --api-key <key>
zenml stack set zenml-cloud-remote
python -m pipelines.run --schedule
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/chat/sessions` | Create a new chat session |
| `GET` | `/chat/sessions` | List sessions for a user |
| `GET` | `/chat/sessions/{id}/messages` | Get session message history |
| `DELETE` | `/chat/sessions/{id}` | Delete a session |
| `POST` | `/chat` | Non-streaming chat (with caching) |
| `POST` | `/chat/stream` | **Streaming SSE chat** (typewriter effect) |
| `GET` | `/health` | Health check + dependency status |

---

## Deployment

### Google Cloud Run

```bash
# Build & push
docker build -t gcr.io/PROJECT/shopify-assistant:latest .
docker push gcr.io/PROJECT/shopify-assistant:latest

# Deploy
gcloud run deploy shopify-assistant \
  --image gcr.io/PROJECT/shopify-assistant:latest \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars "POSTGRES__HOST=...,OPENROUTER_API__KEY=..."
```

The included **GitHub Actions CD workflow** automates this on every push to `main`.




---


</div>
