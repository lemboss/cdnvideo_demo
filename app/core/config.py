from enum import StrEnum
from functools import lru_cache
from typing import Annotated

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Environment(StrEnum):
    LOCAL = "local"
    TESTING = "testing"
    PRODUCTION = "production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "City Geo Service"
    app_version: str = "0.1.0"
    environment: Environment = Environment.LOCAL
    debug: bool = False
    docs_enabled: bool = True
    docs_enabled_in_production: bool = False
    openapi_enabled: bool = True
    log_level: str = "INFO"

    api_key: SecretStr | None = None
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:3000"]
    )
    max_request_body_bytes: int = 1_048_576

    database_url: str = "sqlite+aiosqlite:///./data/cities.db"
    auto_create_schema: bool = False

    redis_url: str = "redis://redis:6379/0"
    redis_timeout_seconds: float = 1.0
    rate_limit_enabled: bool = True
    rate_limit_requests_per_minute: int = 60
    rate_limit_exempt_paths: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["/health"]
    )

    yandex_geocoder_api_key: SecretStr | None = None
    yandex_geocoder_url: str = "https://geocode-maps.yandex.ru/v1"
    http_timeout_seconds: float = 3.0

    @field_validator("cors_origins", "rate_limit_exempt_paths", mode="before")
    @classmethod
    def parse_csv_list(cls, value: object) -> object:
        if isinstance(value, str):
            if not value:
                return []
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("log_level")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        return value.upper()

    @model_validator(mode="after")
    def validate_production_safety(self) -> "Settings":
        if self.environment == Environment.PRODUCTION:
            if self.debug:
                raise ValueError("Debug mode must be disabled in production.")
            if self.api_key is None or not self.api_key.get_secret_value():
                raise ValueError("API_KEY must be configured in production.")
            if (
                self.yandex_geocoder_api_key is None
                or not self.yandex_geocoder_api_key.get_secret_value()
            ):
                raise ValueError("YANDEX_GEOCODER_API_KEY must be configured in production.")
            if "*" in self.cors_origins:
                raise ValueError("Wildcard CORS origins are not allowed in production.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
