"""Application configuration via pydantic-settings."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application configuration.

    Values are loaded from environment variables and/or a .env file
    located in the backend directory.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Database ──
    database_url: str = "postgresql+psycopg://prayaas:prayaas@localhost:5432/prayaas"

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, v: Any) -> Any:
        if isinstance(v, str):
            if v.startswith("postgres://"):
                return v.replace("postgres://", "postgresql+psycopg://", 1)
            if v.startswith("postgresql://") and "+psycopg" not in v and "+asyncpg" not in v:
                return v.replace("postgresql://", "postgresql+psycopg://", 1)
        return v

    # ── Application ──
    app_env: str = "development"
    app_debug: bool = True
    app_title: str = "PRAYAAS Geospatial Intelligence API"
    api_key: str | None = None

    # ── CORS ──
    cors_origins: str | list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    @field_validator("cors_origins", mode="after")
    @classmethod
    def normalize_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            if "," in v:
                return [origin.strip() for origin in v.split(",") if origin.strip()]
            return [v]
        return v

    # ── Spatial ──
    default_srid: int = 4326
    study_region_center_lat: float = 30.43
    study_region_center_lng: float = 79.35

    @property
    def is_testing(self) -> bool:
        return self.app_env == "testing"


@lru_cache
def get_settings() -> Settings:
    return Settings()
