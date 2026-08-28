import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


SCHEMA = """
CREATE TABLE IF NOT EXISTS media (
    media_id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    path TEXT NOT NULL UNIQUE,
    duration_ms INTEGER NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS processing_runs (
    run_id TEXT PRIMARY KEY,
    media_id TEXT NOT NULL REFERENCES media(media_id),
    status TEXT NOT NULL,
    configuration_json TEXT NOT NULL,
    completed_items INTEGER NOT NULL DEFAULT 0,
    failed_items INTEGER NOT NULL DEFAULT 0,
    total_items INTEGER NOT NULL DEFAULT 0,
    error TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS segments (
    segment_id TEXT PRIMARY KEY,
    media_id TEXT NOT NULL REFERENCES media(media_id),
    start_ms INTEGER NOT NULL,
    end_ms INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence (
    run_id TEXT NOT NULL REFERENCES processing_runs(run_id),
    segment_id TEXT NOT NULL REFERENCES segments(segment_id),
    modality TEXT NOT NULL,
    type TEXT NOT NULL,
    content TEXT NOT NULL,
    attributes_json TEXT NOT NULL,
    confidence REAL,
    processor_json TEXT NOT NULL,
    PRIMARY KEY (run_id, segment_id, modality)
);

CREATE TABLE IF NOT EXISTS processing_errors (
    run_id TEXT NOT NULL REFERENCES processing_runs(run_id),
    segment_id TEXT NOT NULL REFERENCES segments(segment_id),
    modality TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (run_id, segment_id, modality)
);

CREATE INDEX IF NOT EXISTS segments_by_media_time
ON segments(media_id, start_ms);

CREATE INDEX IF NOT EXISTS evidence_by_run_segment
ON evidence(run_id, segment_id);

CREATE INDEX IF NOT EXISTS processing_errors_by_run
ON processing_errors(run_id, segment_id);
"""


class Database:
    def __init__(self, path: Path):
        self.path = path

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.executescript(SCHEMA)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")

        try:
            yield connection
            connection.commit()
        finally:
            connection.close()
