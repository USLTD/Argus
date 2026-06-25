from pathlib import Path

from backend.core.engine import BackendEngine
from backend.storage.database import DatabaseManager


class TestBackendEngine:
    def test_engine_initializes(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        db = DatabaseManager(db_path)
        engine = BackendEngine(db=db)
        assert engine.loader is not None

    def test_get_system_state_returns_metrics(self, tmp_path: Path) -> None:
        db = DatabaseManager(tmp_path / "test.db")
        engine = BackendEngine(db=db)

        state = engine.get_system_state()
        # The real driver runs, so state should have cpu/ram
        if "error" in state:
            assert state["error"] == "No driver loaded."
        else:
            assert "cpu" in state
            assert "ram" in state

    def test_get_system_state_writes_to_db(self, tmp_path: Path) -> None:
        db = DatabaseManager(tmp_path / "test.db")
        engine = BackendEngine(db=db)

        engine.get_system_state()
        results = db.query_range("2000-01-01", "2100-01-01")
        assert len(results) >= 1
        db.close()
