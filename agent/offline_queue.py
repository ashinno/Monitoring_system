import sqlite3
import json
import time
from pathlib import Path
from typing import Any


class OfflineQueue:
    """SQLite-backed queue for resilient agent delivery."""

    def __init__(self, db_path: str = "agent_buffer.db"):
        self.db_path = str(Path(db_path))
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS outbound_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    payload TEXT NOT NULL,
                    retries INTEGER NOT NULL DEFAULT 0,
                    next_attempt REAL NOT NULL DEFAULT 0,
                    created_at REAL NOT NULL
                )
                """
            )
            conn.commit()

    def enqueue(self, payload: dict[str, Any]):
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO outbound_queue(payload, retries, next_attempt, created_at) VALUES(?, 0, 0, ?)",
                (json.dumps(payload, default=str), time.time()),
            )
            conn.commit()

    def get_due(self, limit: int = 50) -> list[tuple[int, dict[str, Any], int]]:
        now = time.time()
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, payload, retries FROM outbound_queue WHERE next_attempt <= ? ORDER BY id ASC LIMIT ?",
                (now, max(1, int(limit))),
            ).fetchall()
        result = []
        for row_id, raw_payload, retries in rows:
            try:
                payload = json.loads(raw_payload)
            except Exception:
                payload = {}
            result.append((row_id, payload, int(retries)))
        return result

    def mark_success(self, row_id: int):
        with self._connect() as conn:
            conn.execute("DELETE FROM outbound_queue WHERE id = ?", (int(row_id),))
            conn.commit()

    def mark_failure(self, row_id: int, retries: int):
        # Exponential backoff capped at 5 minutes.
        retry_count = max(0, int(retries)) + 1
        delay = min(300, 2 ** min(retry_count, 8))
        next_attempt = time.time() + delay
        with self._connect() as conn:
            conn.execute(
                "UPDATE outbound_queue SET retries = ?, next_attempt = ? WHERE id = ?",
                (retry_count, next_attempt, int(row_id)),
            )
            conn.commit()

