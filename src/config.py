from pydantic import BaseModel, Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import ClassVar


class PostgresSettings(BaseModel):
    host: str = Field(default="localhost")
    port: int = Field(default=5432)
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


class Settings(BaseSettings):
    postgres: PostgresSettings = PostgresSettings()

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=[".env"],
        env_file_encoding="utf-8",
        extra="ignore",
        env_nested_delimiter="__",
        case_sensitive=False,
        frozen=True,
    )
settings = Settings()
