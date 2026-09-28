"""State and District administrative ORM models."""

from __future__ import annotations

from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import DataMode

if TYPE_CHECKING:
    from app.models.habitation import Habitation


class State(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Indian State or Union Territory."""

    __tablename__ = "states"

    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    data_mode: Mapped[str] = mapped_column(String(20), nullable=False, default=DataMode.DEMO.value)

    # Relationships
    districts: Mapped[list[District]] = relationship(
        "District", back_populates="state", cascade="all, delete-orphan", order_by="District.name"
    )

    def __repr__(self) -> str:
        return f"<State id={self.id!r} code={self.code!r} name={self.name!r}>"


class District(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """District administrative subdivision within a State."""

    __tablename__ = "districts"

    state_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("states.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    headquarters: Mapped[str | None] = mapped_column(String(128), nullable=True)
    data_mode: Mapped[str] = mapped_column(String(20), nullable=False, default=DataMode.DEMO.value)

    # Relationships
    state: Mapped[State] = relationship("State", back_populates="districts")
    habitations: Mapped[list[Habitation]] = relationship(
        "Habitation", back_populates="district_rel", foreign_keys="Habitation.district_id"
    )

    def __repr__(self) -> str:
        return f"<District id={self.id!r} name={self.name!r} state_id={self.state_id!r}>"
