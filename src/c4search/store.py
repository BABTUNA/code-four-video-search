import json
import sqlite3
from pathlib import Path

import numpy as np

from c4search.models import Doc

SCHEMA = """
CREATE TABLE IF NOT EXISTS docs (
    doc_id INTEGER PRIMARY KEY,
    video_id TEXT NOT NULL,
    t_start REAL NOT NULL,
    t_end REAL NOT NULL,
    modality TEXT NOT NULL,
    text TEXT NOT NULL,
    extra TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS docs_by_video_time ON docs(video_id, t_start);
CREATE INDEX IF NOT EXISTS docs_by_modality ON docs(modality);
"""


class Store:
    """Doc records in SQLite; vectors as .npy arrays alongside their doc ids."""

    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.root / "docs.db")
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)

    def add_docs(self, docs: list[Doc]) -> list[int]:
        ids = []
        for doc in docs:
            cursor = self.db.execute(
                "INSERT INTO docs (video_id, t_start, t_end, modality, text, extra)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (doc.video_id, doc.t_start, doc.t_end, doc.modality, doc.text,
                 json.dumps(doc.extra)),
            )
            ids.append(cursor.lastrowid)
        self.db.commit()
        return ids

    def delete_docs(self, video_id: str, modality: str) -> None:
        """Remove one video's docs for one modality, so re-ingest is idempotent."""
        self.db.execute(
            "DELETE FROM docs WHERE video_id = ? AND modality = ?",
            (video_id, modality),
        )
        self.db.commit()

    def docs(
        self,
        video_id: str | None = None,
        modality: str | None = None,
    ) -> list[tuple[int, Doc]]:
        query = "SELECT * FROM docs"
        conditions, params = [], []
        if video_id is not None:
            conditions.append("video_id = ?")
            params.append(video_id)
        if modality is not None:
            conditions.append("modality = ?")
            params.append(modality)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY video_id, t_start"

        results = []
        for row in self.db.execute(query, params):
            doc = Doc(
                video_id=row["video_id"],
                t_start=row["t_start"],
                t_end=row["t_end"],
                modality=row["modality"],
                text=row["text"],
                extra=json.loads(row["extra"]),
            )
            results.append((row["doc_id"], doc))
        return results

    def save_vectors(self, name: str, doc_ids: list[int], vectors: np.ndarray) -> None:
        if len(doc_ids) != len(vectors):
            raise ValueError("doc_ids and vectors must align")
        np.save(self.root / f"{name}.vectors.npy", vectors)
        np.save(self.root / f"{name}.ids.npy", np.array(doc_ids, dtype=np.int64))

    def load_vectors(self, name: str) -> tuple[np.ndarray, np.ndarray]:
        """Returns (doc_ids, vectors)."""
        ids = np.load(self.root / f"{name}.ids.npy")
        vectors = np.load(self.root / f"{name}.vectors.npy")
        return ids, vectors
