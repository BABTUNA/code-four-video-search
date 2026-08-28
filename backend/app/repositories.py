import json
from datetime import UTC, datetime
from uuid import uuid4

from app.database import Database
from app.models import (
    Evidence,
    MediaRecord,
    ProcessingConfiguration,
    ProcessingError,
    ProcessingRun,
    RunStatus,
    Segment,
    SegmentResult,
)


class Repository:
    def __init__(self, database: Database):
        self.database = database

    def save_media(self, media: MediaRecord) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO media (media_id, filename, path, duration_ms, created_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(media_id) DO UPDATE SET
                    filename = excluded.filename,
                    path = excluded.path,
                    duration_ms = excluded.duration_ms
                """,
                (
                    media.media_id,
                    media.filename,
                    media.path,
                    media.duration_ms,
                    media.created_at.isoformat(),
                ),
            )

    def list_media(self) -> list[MediaRecord]:
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM media ORDER BY filename"
            ).fetchall()
        return [self._media_from_row(row) for row in rows]

    def get_media(self, media_id: str) -> MediaRecord | None:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM media WHERE media_id = ?",
                (media_id,),
            ).fetchone()
        return self._media_from_row(row) if row else None

    def create_run(
        self,
        media_id: str,
        configuration: ProcessingConfiguration,
    ) -> ProcessingRun:
        run = ProcessingRun(
            run_id=f"run_{uuid4().hex[:12]}",
            media_id=media_id,
            status=RunStatus.QUEUED,
            configuration=configuration,
            completed_items=0,
            failed_items=0,
            total_items=0,
            error=None,
            created_at=datetime.now(UTC),
        )

        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO processing_runs (
                    run_id, media_id, status, configuration_json,
                    completed_items, failed_items, total_items, error, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run.run_id,
                    run.media_id,
                    run.status.value,
                    run.configuration.model_dump_json(),
                    run.completed_items,
                    run.failed_items,
                    run.total_items,
                    run.error,
                    run.created_at.isoformat(),
                ),
            )
        return run

    def get_run(self, run_id: str) -> ProcessingRun | None:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM processing_runs WHERE run_id = ?",
                (run_id,),
            ).fetchone()
        return self._run_from_row(row) if row else None

    def list_runs(self, media_id: str) -> list[ProcessingRun]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM processing_runs
                WHERE media_id = ?
                ORDER BY created_at DESC
                """,
                (media_id,),
            ).fetchall()
        return [self._run_from_row(row) for row in rows]

    def update_run(
        self,
        run_id: str,
        *,
        status: RunStatus | None = None,
        completed_items: int | None = None,
        failed_items: int | None = None,
        total_items: int | None = None,
        error: str | None = None,
    ) -> None:
        current = self.get_run(run_id)
        if current is None:
            raise ValueError(f"Unknown processing run: {run_id}")

        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE processing_runs
                SET status = ?, completed_items = ?, failed_items = ?,
                    total_items = ?, error = ?
                WHERE run_id = ?
                """,
                (
                    (status or current.status).value,
                    completed_items if completed_items is not None else current.completed_items,
                    failed_items if failed_items is not None else current.failed_items,
                    total_items if total_items is not None else current.total_items,
                    error,
                    run_id,
                ),
            )

    def save_segments(self, segments: list[Segment]) -> None:
        with self.database.connect() as connection:
            connection.executemany(
                """
                INSERT INTO segments (segment_id, media_id, start_ms, end_ms)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(segment_id) DO NOTHING
                """,
                [
                    (
                        segment.segment_id,
                        segment.media_id,
                        segment.start_ms,
                        segment.end_ms,
                    )
                    for segment in segments
                ],
            )

    def save_evidence(self, evidence: Evidence) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO evidence (
                    run_id, segment_id, modality, type, content,
                    attributes_json, confidence, processor_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    evidence.run_id,
                    evidence.segment_id,
                    evidence.modality.value,
                    evidence.type,
                    evidence.content,
                    json.dumps(evidence.attributes),
                    evidence.confidence,
                    evidence.processor.model_dump_json(),
                ),
            )

    def save_processing_error(self, error: ProcessingError) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO processing_errors (
                    run_id, segment_id, modality, message, created_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    error.run_id,
                    error.segment_id,
                    error.modality.value,
                    error.message,
                    error.created_at.isoformat(),
                ),
            )

    def list_processing_errors(self, run_id: str) -> list[ProcessingError]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM processing_errors
                WHERE run_id = ?
                ORDER BY segment_id, modality
                """,
                (run_id,),
            ).fetchall()

        return [
            ProcessingError(
                run_id=row["run_id"],
                segment_id=row["segment_id"],
                modality=row["modality"],
                message=row["message"],
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]

    def list_segment_results(self, run_id: str) -> list[SegmentResult]:
        run = self.get_run(run_id)
        if run is None:
            return []

        with self.database.connect() as connection:
            segment_rows = connection.execute(
                """
                SELECT DISTINCT segments.*
                FROM segments
                JOIN evidence ON evidence.segment_id = segments.segment_id
                WHERE evidence.run_id = ?
                ORDER BY segments.start_ms
                """,
                (run_id,),
            ).fetchall()

            results = []
            for segment_row in segment_rows:
                segment = Segment(**dict(segment_row))
                evidence_rows = connection.execute(
                    """
                    SELECT * FROM evidence
                    WHERE run_id = ? AND segment_id = ?
                    ORDER BY modality
                    """,
                    (run_id, segment.segment_id),
                ).fetchall()

                evidence = [
                    Evidence(
                        run_id=row["run_id"],
                        segment_id=segment.segment_id,
                        media_id=segment.media_id,
                        start_ms=segment.start_ms,
                        end_ms=segment.end_ms,
                        modality=row["modality"],
                        type=row["type"],
                        content=row["content"],
                        attributes=json.loads(row["attributes_json"]),
                        confidence=row["confidence"],
                        processor=json.loads(row["processor_json"]),
                    )
                    for row in evidence_rows
                ]
                results.append(SegmentResult(segment=segment, evidence=evidence))

        return results

    @staticmethod
    def _media_from_row(row: object) -> MediaRecord:
        values = dict(row)
        values["created_at"] = datetime.fromisoformat(values["created_at"])
        return MediaRecord(**values)

    @staticmethod
    def _run_from_row(row: object) -> ProcessingRun:
        values = dict(row)
        values["configuration"] = json.loads(values.pop("configuration_json"))
        values["created_at"] = datetime.fromisoformat(values["created_at"])
        return ProcessingRun(**values)
