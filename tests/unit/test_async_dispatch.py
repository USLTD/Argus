"""Tests for BackendEngine async dispatch modes using a FakeScript helper.

FakeScript duck-types BaseUserScript so the engine's dispatch loop can
exercise BLOCKING, NONBLOCKING, and MIXED execution modes without needing
real Python or Lua scripts.
"""

from __future__ import annotations

import time
from typing import Any

import pytest

from backend.core.engine import BackendEngine
from backend.interfaces.enums import ScriptExecutionMode
from tests.fake_driver import FakeDriver


class FakeScript:
    """Duck-typed stand-in for BaseUserScript with controllable timing & errors.

    Attributes
    ----------
    METADATA : dict
        Plugin metadata dict (name, path, permissions).
    file_path : str
        Path string returned to ``list_scripts()``.
    execution_mode : ScriptExecutionMode
        Current dispatch mode – changed by ``set_script_execution_mode()``.
    _dispatched_events : list[str]
        Accumulator of every ``event_path`` that ``dispatch()`` received.
    _delay : float
        Seconds to sleep inside each ``dispatch()`` call.
    _raise_on_dispatch : bool
        When ``True``, ``dispatch()`` raises ``RuntimeError`` after recording
        the event path (and optional sleep).
    """

    METADATA: dict = {
        "name": "test_script",
        "path": "test.py",
        "permissions": ["SCRIPT.READ"],
    }
    file_path: str = "test.py"
    execution_mode: ScriptExecutionMode = ScriptExecutionMode.NONBLOCKING

    def __init__(
        self,
        delay: float = 0,
        raise_on_dispatch: bool = False,
        execution_mode: ScriptExecutionMode = ScriptExecutionMode.NONBLOCKING,
    ) -> None:
        self._dispatched_events: list[str] = []
        self._output: list[str] = []
        self._delay = delay
        self._raise_on_dispatch = raise_on_dispatch
        self._hooked_events: list[str] = []
        self.execution_mode = execution_mode

    # ── Engine-facing interface ────────────────────────────────────────

    def dispatch(self, event_path: str, data: object = None) -> None:
        """Record the event path, optionally sleep, optionally raise."""
        self._dispatched_events.append(event_path)
        if self._delay > 0:
            time.sleep(self._delay)
        if self._raise_on_dispatch:
            raise RuntimeError("dispatch error")

    def pop_output(self) -> list[str]:
        """Return and clear captured output."""
        out = self._output
        self._output = []
        return out

    @property
    def hooked_events(self) -> list[str]:
        return self._hooked_events

    @property
    def script_type(self) -> str:
        return "python"


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_engine() -> BackendEngine:
    """BackendEngine with a FakeDriver loaded and no active scripts."""
    engine = BackendEngine()
    engine.loader.active_driver = FakeDriver()
    engine.loader.active_scripts = []
    return engine


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestAsyncDispatchModes:
    """Exercises BLOCKING / NONBLOCKING / MIXED script dispatch."""

    # -- helpers ----------------------------------------------------------

    @staticmethod
    def _wait_for_futures(engine: BackendEngine, timeout: float = 5.0) -> None:
        """Block until every pending future in the engine is done."""
        with engine._lock:
            futures = list(engine._futures)
        for f in futures:
            f.result(timeout=timeout)

    # -- Test 1: NONBLOCKING ---------------------------------------------

    def test_nonblocking_does_not_block_tick(self, fake_engine: BackendEngine) -> None:
        """NONBLOCKING dispatch submits to the thread pool and returns immediately."""
        script = FakeScript(
            delay=0.3, execution_mode=ScriptExecutionMode.NONBLOCKING
        )
        fake_engine.loader.active_scripts = [script]  # type: ignore[assignment]

        start = time.monotonic()
        fake_engine.tick()
        elapsed = time.monotonic() - start

        # The main thread should return long before the script's sleep completes
        assert elapsed < 0.2, (
            f"NONBLOCKING tick took {elapsed:.3f}s, expected < 0.2s"
        )

        # Wait for the background dispatch to finish, then verify events
        self._wait_for_futures(fake_engine)
        assert len(script._dispatched_events) > 0

    # -- Test 2: BLOCKING -------------------------------------------------

    def test_blocking_blocks_tick(self, fake_engine: BackendEngine) -> None:
        """BLOCKING dispatch runs synchronously and waits for every event."""
        script = FakeScript(
            delay=0.08, execution_mode=ScriptExecutionMode.BLOCKING
        )
        fake_engine.loader.active_scripts = [script]  # type: ignore[assignment]

        start = time.monotonic()
        fake_engine.tick()
        elapsed = time.monotonic() - start

        # The tick should have waited for every dispatch call (each sleeps)
        # With 7 non-None events × 0.08s ≈ 0.56s; assert at least 0.05s
        assert elapsed >= 0.05, (
            f"BLOCKING tick took {elapsed:.3f}s, expected ≥ 0.05s"
        )
        assert len(script._dispatched_events) > 0

    # -- Test 3: MIXED (short timeout – runs inline) ---------------------

    def test_mixed_short_timeout_runs_inline(
        self, fake_engine: BackendEngine
    ) -> None:
        """MIXED dispatch runs inline when the script finishes within its timeout."""
        script = FakeScript(
            delay=0.01, execution_mode=ScriptExecutionMode.MIXED
        )
        fake_engine.loader.active_scripts = [script]  # type: ignore[assignment]
        # Reminder: script_timeout_ms defaults to 5000 – very generous

        start = time.monotonic()
        fake_engine.tick()
        elapsed = time.monotonic() - start

        # With 7 non-None events × 0.01s ≈ 0.07s, plus overhead
        assert elapsed < 0.2, (
            f"MIXED tick took {elapsed:.3f}s, expected < 0.2s"
        )
        assert len(script._dispatched_events) > 0

        # The future completed inline, so it must NOT be in _futures
        with fake_engine._lock:
            assert len(fake_engine._futures) == 0

    # -- Test 4: Exception in thread pool is caught ----------------------

    def test_script_exception_in_thread_pool_caught(
        self, fake_engine: BackendEngine
    ) -> None:
        """Exceptions raised inside a NONBLOCKING dispatch are silently caught."""
        script = FakeScript(
            raise_on_dispatch=True, execution_mode=ScriptExecutionMode.NONBLOCKING
        )
        fake_engine.loader.active_scripts = [script]  # type: ignore[assignment]

        # Must NOT raise – the exception is caught inside _dispatch_script
        fake_engine.tick()

        # Give the thread a moment to execute and be collected
        self._wait_for_futures(fake_engine, timeout=3.0)

        # The dispatch was attempted (recorded before the raise)
        assert len(script._dispatched_events) > 0

        # The completed/failed future is cleaned up by _collect_pending_output
        with fake_engine._lock:
            assert len(fake_engine._futures) == 0

    # -- Test 5: set_script_execution_mode() persists --------------------

    def test_set_script_execution_mode_persists_across_ticks(
        self, fake_engine: BackendEngine
    ) -> None:
        """Changing a script's execution mode takes effect on the next tick."""
        script = FakeScript(
            delay=0.08, execution_mode=ScriptExecutionMode.NONBLOCKING
        )
        fake_engine.loader.active_scripts = [script]  # type: ignore[assignment]

        # Switch to BLOCKING
        fake_engine.set_script_execution_mode(
            "test_script", ScriptExecutionMode.BLOCKING
        )
        assert script.execution_mode == ScriptExecutionMode.BLOCKING

        # The next tick should now block
        start = time.monotonic()
        fake_engine.tick()
        elapsed = time.monotonic() - start
        assert elapsed >= 0.05, (
            f"BLOCKING tick after mode change took {elapsed:.3f}s, expected ≥ 0.05s"
        )

    # -- Test 6: list_scripts() returns metadata -------------------------

    def test_list_scripts_returns_correct_metadata(
        self, fake_engine: BackendEngine
    ) -> None:
        """list_scripts() returns ScriptInfo matching the loaded script."""
        script = FakeScript()
        fake_engine.loader.active_scripts = [script]  # type: ignore[assignment]

        scripts = fake_engine.list_scripts()
        assert len(scripts) == 1
        info = scripts[0]
        assert info["name"] == "test_script"
        assert info["path"] == "test.py"
        assert info["type"] == "python"
        assert info["execution_mode"] == ScriptExecutionMode.NONBLOCKING
        assert info["permissions"] == ["SCRIPT.READ"]
        assert info["hooked_events"] == []
