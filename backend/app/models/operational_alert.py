"""Operational Alert ORM model — real-time event feed."""

from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class OperationalAlert(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """An operational event alert in the decision-support feed."""

    __tablename__ = "operational_alerts"

    message: Mapped[str] = mapped_column(String(1024), nullable=False)
    type: Mapped[str] = mapped_column(
        String(30), nullable=False, index=True,
        doc="ESCALATION | WEATHER | VERIFICATION | PRIORITY_CHANGE | FIELD_UPDATE | SYSTEM",
    )
    severity: Mapped[str] = mapped_column(
        String(20), nullable=False, default="WATCH",
        doc="CRITICAL | HIGH | WATCH | SAFE",
    )
    timestamp: Mapped[str] = mapped_column(String(30), nullable=False, doc="ISO 8601 datetime")

    habitation_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("habitations.id", ondelete="SET NULL"), nullable=True,
    )
    read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    def __repr__(self) -> str:
        return f"<OperationalAlert id={self.id!r} severity={self.severity!r}>"
