"""
Application configuration using pydantic-settings.

Loads configuration from environment variables with validation and defaults.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "IRIS Digital Invoicing"
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    secret_key: str = Field(..., min_length=32)

    # Database
    database_url: PostgresDsn

    # JWT
    jwt_secret_key: str = Field(..., min_length=32)
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440  # 24 hours

    # FBR/IRIS Integration
    fbr_sandbox_url: str = "https://gw.fbr.gov.pk/di_data/v1/di/postinvoicedata_sb"
    fbr_production_url: str = ""
    fbr_timeout_seconds: int = 30
    fbr_max_retries: int = 3
    fbr_retry_delay_seconds: int = 2
    fbr_auth_token: str = Field(default="", alias="FBR_SANDBOX_TOKEN", description="FBR Bearer Token")
    fbr_sandbox_invoice_detail_url: str = Field(default="", description="Validation Endpoint")
    fbr_sandbox_invoice_detail_token: str = Field(default="", description="Validation Token")

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.app_env == "production"

    @property
    def fbr_url(self) -> str:
        """Get the appropriate FBR URL based on environment."""
        if self.is_production and self.fbr_production_url:
            return self.fbr_production_url
        return self.fbr_sandbox_url


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
