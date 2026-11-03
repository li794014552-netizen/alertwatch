from __future__ import annotations

import json
import sqlite3
from pathlib import Path


class SnapshotStore:
    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS snapshots (
                    job TEXT PRIMARY KEY,
                    values_json TEXT NOT NULL
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._path)

    def get(self, job: str) -> dict[str, str] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT values_json FROM snapshots WHERE job = ?",
                (job,),
            ).fetchone()
        if row is None:
            return None
        data = json.loads(row[0])
        return {str(k): str(v) for k, v in data.items()}

    def put(self, job: str, values: dict[str, str]) -> None:
        payload = json.dumps(values, ensure_ascii=False, sort_keys=True)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO snapshots (job, values_json)
                VALUES (?, ?)
                ON CONFLICT(job) DO UPDATE SET values_json = excluded.values_json
                """,
                (job, payload),
            )
            conn.commit()
