import os
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings."""

    service_name: str = "app"
    """Name of the application service."""

    @model_validator(mode="before")
    @classmethod
    def set_service_name_from_env(cls, values):
        if not values.get("service_name"):
            otel_name = os.getenv("OTEL_SERVICE_NAME")
            if otel_name:
                values["service_name"] = otel_name
        return values

    environment: Literal["development", "staging", "production"] = "development"
    """Application environment (development, staging, production)."""

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "DEBUG"
    """Logging level for the application."""

    bedrock_model_id: str = "eu.amazon.nova-lite-v1:0"
    """Default model ID to use for Bedrock LLM calls"""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


# @lru_cache
def get_settings() -> Settings:
    settings = Settings()
    return settings
