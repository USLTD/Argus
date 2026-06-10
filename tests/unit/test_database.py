from pathlib import Path

from backend.interfaces.caps import CPUMetrics, RAMMetrics, SystemMetrics
from backend.storage.database import DatabaseManager


class TestDatabaseManager:
    def test_schema_creates_tables(self, tmp_path: Path) -> None:
        db = DatabaseManager(tmp_path / "test.db")
        # metrics table exists
        row = db._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='metrics'"
        ).fetchone()
        assert row is not None
        # alerts table should NOT exist
        alerts = db._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='alerts'"
        ).fetchone()
        assert alerts is None
        db.close()

    def test_write_and_query(self, tmp_path: Path) -> None:
        db = DatabaseManager(tmp_path / "test.db")
        cpu = CPUMetrics(physical_cores=2, logical_cores=4, usage_percent=50.0)
        ram = RAMMetrics(
            total_bytes=1000, used_bytes=500, available_bytes=500, percent=50.0
        )
        metrics = SystemMetrics(cpu=cpu, ram=ram)

        db.write_snapshot(metrics)
        results = db.query_range("2000-01-01", "2100-01-01")
        assert len(results) == 1
        assert "cpu" in results[0]["payload"]
        db.close()

    def test_wal_mode(self, tmp_path: Path) -> None:
        db = DatabaseManager(tmp_path / "test.db")
        # Check journal mode is WAL
        mode = db._conn.execute("PRAGMA journal_mode").fetchone()
        assert mode[0].lower() == "wal"
        db.close()
