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




class Settings(BaseSettings):
    postgres: PostgresSettings = PostgresSettings()
    qdrant: QdrantSettings = QdrantSettings()

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=[".env"],
        env_file_encoding="utf-8",
        extra="ignore",
        env_nested_delimiter="__",
        case_sensitive=False,
        frozen=True,
    )

settings = Settings()
