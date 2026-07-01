"""Basic smoke test: load the backend, run 3 poll cycles without crash."""

import sys
from pathlib import Path

from backend.core.engine import BackendEngine


class TestSmoke:
    def test_three_poll_cycles(self, tmp_path: Path) -> None:
        if sys.platform not in ("win32", "linux"):
            return  # Smoke test only on supported platforms

        engine = BackendEngine()

        assert engine.loader.active_driver is not None, "No driver loaded"

        for _ in range(3):
            state = engine.get_system_state()
            assert "error" not in state, state["error"]
            cpu_metrics = state["cpu"].get("metrics", [{}])
            ram_metrics = state["ram"].get("metrics", [{}])
            assert cpu_metrics[0].get("usage_percent") is not None
            assert ram_metrics[0].get("percent") is not None
