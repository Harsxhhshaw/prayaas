"""FastAPI dependency functions."""

from __future__ import annotations

from collections.abc import Generator
from fastapi import Header, HTTPException, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db


def verify_api_key(x_api_key: str | None = Header(None, alias="X-API-Key")) -> str | None:
    """Verifies X-API-Key header when configured in production.
    If no api_key is configured or app_env is development, allows pass-through.
    """
    settings = get_settings()
    configured_key = settings.api_key
    if not configured_key or settings.app_env == "development":
        return x_api_key

    if not x_api_key or x_api_key != configured_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-API-Key header",
        )
    return x_api_key


__all__ = ["get_db", "verify_api_key"]
