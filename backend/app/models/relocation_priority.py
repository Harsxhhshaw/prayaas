"""Relocation Priority ORM model — links habitations to candidate sites."""

from __future__ import annotations

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class RelocationPriority(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A prioritized relocation entry linking a habitation to an optional site."""

    __tablename__ = "relocation_priorities"

    habitation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("habitations.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    habitation_name: Mapped[str] = mapped_column(String(255), nullable=False)
    urgency: Mapped[str] = mapped_column(
        String(20), nullable=False, default="MEDIUM_TERM",
        doc="IMMEDIATE | SHORT_TERM | MEDIUM_TERM",
    )
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    population: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    district: Mapped[str] = mapped_column(String(128), nullable=False)

    # ── Optional assigned site ──
    assigned_site_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("candidate_sites.id", ondelete="SET NULL"), nullable=True,
    )
    assigned_site_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # ── Planning ──
    estimated_cost: Mapped[float | None] = mapped_column(Float, nullable=True, doc="in lakhs INR")
    timeline_months: Mapped[int | None] = mapped_column(Integer, nullable=True)

    def __repr__(self) -> str:
        return f"<RelocationPriority hab={self.habitation_name!r} urgency={self.urgency!r}>"
