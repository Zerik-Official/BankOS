"""Application settings loaded from environment variables."""

# Standard library
from functools import lru_cache

# Third-party
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration of the API."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "BankOS API"
    environment: str = "local"
    api_v1_prefix: str = "/api/v1"
    docs_enabled: bool = True
    log_level: str = "INFO"

    database_url: str = "sqlite:///./data/bankos.db"

    jwt_secret_key: str = "dev-insecure-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 60

    cors_origins: str = "http://localhost:8000,http://localhost:5173"

    rate_limit_auth_per_minute: int = 10
    rate_limit_financial_per_minute: int = 30
    rate_limit_ip_per_minute: int = 120
    webhook_timeout_seconds: float = Field(default=5.0, gt=0)

    @property
    def cors_origin_list(self) -> list[str]:
        """Return the allowed CORS origins as a list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return the cached settings instance."""
    return Settings()
