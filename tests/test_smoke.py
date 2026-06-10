"""Basic smoke test: load the backend, run 3 poll cycles without crash."""

import sys
from pathlib import Path

from backend.core.engine import BackendEngine
from backend.storage.database import DatabaseManager


class TestSmoke:
    def test_three_poll_cycles(self, tmp_path: Path) -> None:
        if sys.platform not in ("win32", "linux"):
            return  # Smoke test only on supported platforms

        db = DatabaseManager(tmp_path / "smoke.db")
        engine = BackendEngine(db=db)

        assert engine.loader.active_driver is not None, "No driver loaded"

        for _ in range(3):
            state = engine.get_system_state()
            assert "error" not in state, state["error"]
            assert state["cpu"]["usage_percent"] is not None
            assert state["ram"]["percent"] is not None

        db.close()
