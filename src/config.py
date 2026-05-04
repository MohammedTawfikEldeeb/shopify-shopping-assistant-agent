from pydantic import BaseModel, Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import ClassVar


class PostgresSettings(BaseModel):
    host: str = Field(default="localhost")
    port: int = Field(default=5433)
    database: str = Field(default="shopify_assistant")
    user: str = Field(default="shopify_user")
    password: str = Field(default="shopify_password")

    @computed_field
    @property
    def url(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    @computed_field
    @property
    def async_url(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


class QdrantSettings(BaseModel):
    environment: str = Field(default="local")  # 'local' or 'cloud'
    url: str | None = Field(default=None)  # Cloud URL only
    host: str = Field(default="localhost")  # Local host only
    port: int = Field(default=6333)  # Local port only
    api_key: str | None = Field(default=None)
    collection_name: str = Field(default="products")
    vector_size: int = Field(default=384)
    distance_metric: str = Field(default="cosine")
    prefer_grpc: bool = Field(default=False)
    https: bool | None = Field(default=None)


class LLMSettings(BaseModel):
    provider: str = Field(default="groq" , description="The LLM provider backend")

class LLMModelSettings(BaseModel):
    name: str = Field(default="openai/gpt-oss-120b" , description="The model name for the configured LLM provider")

class OpenRouterAPISettings(BaseModel):
    key: str | None = Field(default=None , description="The OpenRouter API key")
    base_url: str = Field(default="https://openrouter.ai/api/v1" , description="The OpenRouter API base URL")

class GroqAPISettings(BaseModel):
    key: str | None = Field(default=None , description="The Groq API key")
    base_url: str = Field(default="https://api.groq.com/openai/v1" , description="The Groq API base URL")

class OpikSettings(BaseModel):
    api_key: str = Field(default="", description="Opik API Key")
    project_name: str = Field(default="shopify-shopping-assistant-agent", description="Opik Project Name")

class SemanticCacheSettings(BaseModel):
    enabled: bool = Field(default=True, description="Enable or disable semantic caching")
    similarity_threshold: float = Field(default=0.92, description="Minimum cosine similarity for cache hit")
    ttl_seconds: int = Field(default=86400, description="Cache entry time-to-live in seconds")

class Settings(BaseSettings):
    vector_db_provider: str = Field(default="PGVECTOR")
    postgres: PostgresSettings = PostgresSettings()
    qdrant: QdrantSettings = QdrantSettings()
    llm: LLMSettings = LLMSettings()
    llm_model: LLMModelSettings = LLMModelSettings()
    groq_api: GroqAPISettings = GroqAPISettings()
    openrouter_api: OpenRouterAPISettings = OpenRouterAPISettings()
    opik: OpikSettings = OpikSettings()
    semantic_cache: SemanticCacheSettings = SemanticCacheSettings()

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=[".env"],
        env_file_encoding="utf-8",
        extra="ignore",
        env_nested_delimiter="__",
        case_sensitive=False,
        frozen=True,
    )

settings = Settings()

def get_settings() -> Settings:
    return settings
