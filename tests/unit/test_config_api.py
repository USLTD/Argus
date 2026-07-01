"""Tests for BackendEngine.set_config() and BackendEngine.get_config().

Uses a real BackendEngine with a FakeDriver attached — no mocks on the engine.
A temp config path is set via ``ARGUS_CONFIG_PATH`` so that ``config.save()``
writes to a throw-away location.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from backend.core.engine import BackendEngine
from tests.fake_driver import FakeDriver


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def engine(tmp_path: Path, request: pytest.FixtureRequest) -> BackendEngine:
    """BackendEngine with a FakeDriver and a throw-away config YAML path."""
    config_path = tmp_path / "config.yaml"
    os.environ["ARGUS_CONFIG_PATH"] = str(config_path)
    request.addfinalizer(lambda: os.environ.pop("ARGUS_CONFIG_PATH", None))
    eng = BackendEngine()
    eng.loader.active_driver = FakeDriver()
    eng.loader.active_scripts = []
    return eng


# ---------------------------------------------------------------------------
# Tests — set_config
# ---------------------------------------------------------------------------


class TestSetConfig:
    def test_set_known_field(self, engine: BackendEngine) -> None:
        """set_config updates BackendEngine.config for a valid field."""
        engine.set_config("poll_interval_ms", 2000)
        assert engine.config.poll_interval_ms == 2000

    def test_set_unknown_field_raises(self, engine: BackendEngine) -> None:
        """set_config raises ValueError for a field that does not exist."""
        with pytest.raises(ValueError, match="Unknown config field"):
            engine.set_config("nonexistent_field", "value")

    def test_set_invalid_type_raises(self, engine: BackendEngine) -> None:
        """set_config raises ValueError when value fails type validation."""
        with pytest.raises(ValueError, match="Invalid value for 'poll_interval_ms'"):
            engine.set_config("poll_interval_ms", "notanint")

    def test_set_script_batch_size_resizes_pool(self, engine: BackendEngine) -> None:
        """script_batch_size replaces the thread-pool executor."""
        old_executor = engine._executor
        original_workers = old_executor._max_workers
        engine.set_config("script_batch_size", 8)
        assert engine._executor._max_workers == 8
        assert engine._executor._max_workers != original_workers
        assert engine._executor is not old_executor

    def test_set_process_tick_interval_resets_counter(
        self, engine: BackendEngine
    ) -> None:
        """process_tick_interval resets _process_tick_counter to 0."""
        engine._process_tick_counter = 42
        engine.set_config("process_tick_interval", 10)
        assert engine._process_tick_counter == 0


# ---------------------------------------------------------------------------
# Tests — get_config
# ---------------------------------------------------------------------------


class TestGetConfig:
    def test_get_config_returns_all_fields(self, engine: BackendEngine) -> None:
        """get_config returns all ArgusConfig fields."""
        cfg = engine.get_config()
        expected_keys = {
            "driver_override",
            "poll_interval_ms",
            "script_compatibility_default",
            "script_batch_size",
            "script_timeout_ms",
            "script_execution_mode",
            "process_tick_interval",
            "subsystem_enabled",
            "subsystem_intervals",
            "subsystem_timeout",
        }
        assert set(cfg.keys()) == expected_keys

    def test_get_config_after_set_reflects_change(self, engine: BackendEngine) -> None:
        """set_config then get_config shows the updated value."""
        engine.set_config("poll_interval_ms", 2000)
        cfg = engine.get_config()
        assert cfg["poll_interval_ms"] == 2000
