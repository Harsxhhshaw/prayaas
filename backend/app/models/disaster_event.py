"""DisasterEvent ORM model — historical and real-time hazard incident catalog."""

from __future__ import annotations

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from geoalchemy2 import Geometry

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import DataMode, HazardType, RiskClassification


class DisasterEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Historical or real-time disaster event record."""

    __tablename__ = "disaster_events"

    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    hazard_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=HazardType.LANDSLIDE.value,
        doc="LANDSLIDE | FLOOD | CLOUDBURST | EARTHQUAKE | AVALANCHE",
    )
    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=RiskClassification.CRITICAL.value,
        doc="CRITICAL | HIGH | WATCH | SAFE",
    )
    event_date: Mapped[str] = mapped_column(String(20), nullable=False, doc="ISO Date YYYY-MM-DD")
    district: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    geom: Mapped[str | None] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=True,
    )
    fatalities: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    displaced_persons: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    data_mode: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=DataMode.DEMO.value,
        doc="DEMO | REALTIME | HISTORICAL | SIMULATED",
    )

    def __repr__(self) -> str:
        return f"<DisasterEvent id={self.id!r} title={self.title!r} date={self.event_date!r}>"
