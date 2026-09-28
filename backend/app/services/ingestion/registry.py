"""Source registry and freshness evaluation service."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.data_source import DataSource
from app.models.enums import SourceFreshness
from app.schemas.data_source import DataSourceFreshnessItem, FreshnessReportResponse


def evaluate_source_freshness(source: DataSource, now: datetime | None = None) -> tuple[SourceFreshness, bool]:
    """Evaluates the freshness of a DataSource based on last_successful_ingestion and expected_refresh_seconds.

    Returns:
        (SourceFreshness, is_stale)
    """
    if now is None:
        now = datetime.now(timezone.utc)

    timestamp = source.last_successful_ingestion
    if timestamp is None:
        # Fallback to last_sync if available
        if source.last_sync:
            try:
                # Try parsing ISO
                timestamp = datetime.fromisoformat(source.last_sync.replace("Z", "+00:00"))
            except Exception:
                timestamp = None

    if timestamp is None:
        return SourceFreshness.UNKNOWN, True

    # Make sure timestamp is timezone-aware
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)

    age_seconds = (now - timestamp).total_seconds()
    if age_seconds < 0:
        age_seconds = 0

    expected = source.expected_refresh_seconds or 86400  # Default 24 hours

    if age_seconds <= expected:
        return SourceFreshness.CURRENT, False
    elif age_seconds <= expected * 3:
        return SourceFreshness.AGING, False
    else:
        return SourceFreshness.STALE, True


class SourceRegistryService:
    """Manages registered geospatial sources and freshness audits."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_freshness_report(self) -> FreshnessReportResponse:
        sources = self.db.query(DataSource).order_by(DataSource.name).all()
        now = datetime.now(timezone.utc)
        items: list[DataSourceFreshnessItem] = []
        stale_count = 0

        for s in sources:
            freshness, is_stale = evaluate_source_freshness(s, now)
            if is_stale:
                stale_count += 1
            items.append(
                DataSourceFreshnessItem(
                    id=s.id,
                    name=s.name,
                    provider=s.provider,
                    type=s.type,
                    freshness=freshness.value,
                    lastSuccessfulIngestion=s.last_successful_ingestion.isoformat() if s.last_successful_ingestion else (s.last_sync or None),
                    expectedRefreshSeconds=s.expected_refresh_seconds,
                    dataMode=s.data_mode,
                    isStale=is_stale,
                )
            )

        return FreshnessReportResponse(
            items=items,
            total=len(items),
            stale_count=stale_count,
        )

    def get_or_create_source(
        self,
        id: str,
        name: str,
        provider: str,
        type: str,
        data_mode: str,
        verified_url: str | None = None,
        license: str | None = None,
        expected_refresh_seconds: int = 86400,
        metadata_json: dict[str, Any] | None = None,
    ) -> DataSource:
        source = self.db.query(DataSource).filter(DataSource.id == id).first()
        if not source:
            source = DataSource(
                id=id,
                name=name,
                provider=provider,
                type=type,
                data_mode=data_mode,
                verified_url=verified_url,
                license=license,
                expected_refresh_seconds=expected_refresh_seconds,
                status="ACTIVE",
                metadata_json=metadata_json or {},
            )
            self.db.add(source)
            self.db.commit()
            self.db.refresh(source)
        return source
