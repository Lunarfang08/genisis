from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="GENESIS_",
        env_file=(".env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: Literal["development", "test", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = Field(default=8000, ge=1, le=65535)
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:3000"]
    database_url: str = "postgresql+asyncpg://genesis:genesis@localhost:5432/genesis"
    redis_url: str = "redis://localhost:6379/0"
    health_timeout_seconds: float = Field(default=2.0, gt=0.0, le=10.0)
    auth_secret_key: str = Field(
        default="development-only-change-me-at-least-32-characters",
        min_length=32,
    )
    access_token_minutes: int = Field(default=15, ge=1, le=60)
    refresh_token_days: int = Field(default=30, ge=1, le=90)
    cookie_secure: bool = False
    cookie_domain: str | None = None
    auth_rate_limit: int = Field(default=10, ge=1, le=100)
    request_size_limit_bytes: int = Field(default=1_048_576, ge=16_384, le=10_485_760)
    trusted_hosts: list[str] = ["localhost", "127.0.0.1", "testserver"]
    ai_enabled: bool = False
    ai_provider: Literal["mock", "groq", "ollama", "openai", "anthropic"] = "mock"
    ai_model: str = "llama-3.3-70b-versatile"
    ai_daily_call_budget: int = Field(default=5, ge=0, le=1_000)
    ai_timeout_seconds: float = Field(default=15.0, gt=0.0, le=120.0)
    groq_api_key: str | None = None
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    ollama_base_url: str = "http://localhost:11434"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @model_validator(mode="after")
    def reject_wildcard_cors(self) -> "Settings":
        if "*" in self.cors_origins:
            raise ValueError("Wildcard CORS origins are not allowed")
        if self.is_production and self.auth_secret_key.startswith("development-only"):
            raise ValueError("GENESIS_AUTH_SECRET_KEY must be changed in production")
        if self.is_production and not self.cookie_secure:
            raise ValueError("GENESIS_COOKIE_SECURE must be enabled in production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
