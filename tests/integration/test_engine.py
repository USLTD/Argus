from pathlib import Path

from backend.core.engine import BackendEngine


class TestBackendEngine:
    def test_engine_initializes(self, tmp_path: Path) -> None:
        engine = BackendEngine()
        assert engine.loader is not None

    def test_get_system_state_returns_metrics(self, tmp_path: Path) -> None:
        engine = BackendEngine()

        state = engine.get_system_state()
        # The real driver runs, so state should have cpu/ram
        if "error" in state:
            assert state["error"] == "No driver loaded."
        else:
            assert "cpu" in state
            assert "ram" in state

    def test_tick_returns_snapshot(self, tmp_path: Path) -> None:
        engine = BackendEngine()

        snapshot = engine.tick()
        assert hasattr(snapshot, "cpu")
        assert hasattr(snapshot, "memory")

    def test_tick_users_returns_expected_type(self, tmp_path: Path) -> None:
        engine = BackendEngine()

        result = engine.tick_users()
        from backend.interfaces.caps import MetricsCollection
        from backend.interfaces.sentinels import Unavailable

        # Real driver may or may not support users; either type is valid
        assert isinstance(result, (MetricsCollection, Unavailable))

    def test_last_tick_duration_property(self, tmp_path: Path) -> None:
        engine = BackendEngine()

        assert isinstance(engine.last_tick_duration, float)
        assert engine.last_tick_duration == 0.0
