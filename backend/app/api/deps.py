"""FastAPI dependency functions."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy.orm import Session

from app.database import get_db

# Re-export so routes do: Depends(get_db)
__all__ = ["get_db"]
