import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from backend.core.paths import resolve_db_path
from backend.interfaces.caps import SystemMetrics


class DatabaseManager:
    def __init__(self, db_path: Path | None = None) -> None:
        self._path = db_path or resolve_db_path()
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self._path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                captured_at TEXT NOT NULL,
                payload TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_metrics_captured_at ON metrics(captured_at);
        """)
        self._conn.commit()

    def write_snapshot(self, metrics: SystemMetrics) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            "INSERT INTO metrics (captured_at, payload) VALUES (?, ?)",
            (now, metrics.model_dump_json()),
        )
        self._conn.commit()

    def query_range(self, start: str, end: str) -> list[dict[str, str]]:
        rows = self._conn.execute(
            "SELECT captured_at, payload FROM metrics WHERE captured_at BETWEEN ? AND ? ORDER BY captured_at ASC",
            (start, end),
        ).fetchall()
        return [{"captured_at": row[0], "payload": row[1]} for row in rows]

    def close(self) -> None:
        self._conn.close()
