"""Base connector for geospatial and environmental data ingestion pipelines."""

from __future__ import annotations

import traceback
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Generator
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.data_source import DataSource
from app.models.enums import IngestionStatus
from app.models.ingestion import IngestionRun


class IngestionContext:
    """Tracks stats and state during an ingestion execution."""

    def __init__(self, run: IngestionRun) -> None:
        self.run = run
        self.received = 0
        self.inserted = 0
        self.updated = 0
        self.skipped = 0
        self.rejected = 0
        self.metadata: dict[str, Any] = {}

    def inc_received(self, count: int = 1) -> None:
        self.received += count

    def inc_inserted(self, count: int = 1) -> None:
        self.inserted += count

    def inc_updated(self, count: int = 1) -> None:
        self.updated += count

    def inc_skipped(self, count: int = 1) -> None:
        self.skipped += count

    def inc_rejected(self, count: int = 1) -> None:
        self.rejected += count

    def set_metadata(self, key: str, value: Any) -> None:
        self.metadata[key] = value


class BaseIngestionConnector:
    """Abstract base connector managing IngestionRun lifecycle and audit tracking."""

    def __init__(self, db: Session, ingestion_type: str, source_id: str | None = None, data_mode: str = "DEMO") -> None:
        self.db = db
        self.ingestion_type = ingestion_type
        self.source_id = source_id
        self.data_mode = data_mode

    @contextmanager
    def run_context(self) -> Generator[IngestionContext, None, None]:
        now = datetime.now(timezone.utc)
        run = IngestionRun(
            id=str(uuid4()),
            source_id=self.source_id,
            ingestion_type=self.ingestion_type,
            started_at=now,
            status=IngestionStatus.RUNNING.value,
            data_mode=self.data_mode,
            ingestion_metadata={},
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)

        ctx = IngestionContext(run)
        try:
            yield ctx
            # Completed successfully
            finished_at = datetime.now(timezone.utc)
            run.finished_at = finished_at
            run.status = IngestionStatus.COMPLETED.value
            run.records_received = ctx.received
            run.records_inserted = ctx.inserted
            run.records_updated = ctx.updated
            run.records_skipped = ctx.skipped
            run.records_rejected = ctx.rejected
            run.ingestion_metadata = ctx.metadata

            if self.source_id:
                source = self.db.query(DataSource).filter(DataSource.id == self.source_id).first()
                if source:
                    source.last_ingested_at = finished_at
                    source.last_successful_ingestion = finished_at
                    source.records_count = (source.records_count or 0) + ctx.inserted
                    source.status = "ACTIVE"
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            finished_at = datetime.now(timezone.utc)
            run.finished_at = finished_at
            run.status = IngestionStatus.FAILED.value
            run.error_message = f"{str(exc)}\n{traceback.format_exc()[:1000]}"
            run.records_received = ctx.received
            run.records_inserted = ctx.inserted
            run.records_updated = ctx.updated
            run.records_skipped = ctx.skipped
            run.records_rejected = ctx.rejected
            run.ingestion_metadata = ctx.metadata

            if self.source_id:
                source = self.db.query(DataSource).filter(DataSource.id == self.source_id).first()
                if source:
                    source.last_ingested_at = finished_at
                    source.status = "DEGRADED"
            self.db.commit()
            raise
