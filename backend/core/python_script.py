"""
PythonScriptWrapper — adapts a Python user script for engine dispatch.

Every script gets its own ``argus`` namespace via :func:`create_argus_namespace`,
so callbacks registered by one script never leak into another.

Script authors write::

    import argus

    @argus.lifecycle.on_load
    def setup(ctx):
        print("loaded!")

    @argus.events.cpu.on_tick
    def on_cpu(data):
        print(f"CPU: {data['usage_percent']}%")
"""

from __future__ import annotations

import sys
from pathlib import Path
from time import monotonic_ns
from types import ModuleType
from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.interfaces.contexts import ScriptContext

from backend.core.argus_runtime import (
    create_argus_namespace,
    extract_registered_callbacks,
)
from backend.interfaces.enums import ScriptExecutionMode
from backend.interfaces.plugins import BaseDriver, BaseUserScript, PluginMeta


class PythonScriptWrapper(BaseUserScript):
    """Wraps a Python user script file for the engine.

    Takes a ``file_path`` and ``meta`` (metadata dict), and provides
    ``load()``, ``dispatch()``, ``trigger_load()``, ``trigger_unload()``,
    and ``pop_output()`` methods consumable by the engine's event loop.
    """

    def __init__(
        self,
        file_path: Path,
        meta: PluginMeta,
        execution_mode: ScriptExecutionMode = ScriptExecutionMode.NONBLOCKING,
    ) -> None:
        self.file_path = file_path
        self.METADATA = meta
        self.execution_mode = execution_mode
        self._driver: BaseDriver | None = None
        self._argus_mod: ModuleType | None = None
        self._lifecycle_callbacks: dict[str, Callable[..., object]] = {}
        self._event_callbacks: dict[str, Callable[..., object]] = {}
        self._cooldown_until: int = 0
        self._loaded = False

    # ------------------------------------------------------------------
    # Introspection properties
    # ------------------------------------------------------------------

    @property
    def hooked_events(self) -> list[str]:
        """Event paths this script has registered callbacks for."""
        return list(self._event_callbacks.keys())

    @property
    def script_type(self) -> str:
        """Returns ``\"python\"`` — used by list_scripts() to identify the language."""
        return "python"

    # ------------------------------------------------------------------
    # Engine interface
    # ------------------------------------------------------------------

    def bind_driver(self, driver: BaseDriver | None) -> None:
        self._driver = driver

    def load(self) -> None:
        """Execute the script file inside an injected ``argus`` namespace."""
        if self._loaded:
            return

        assert self.file_path is not None
        source = self.file_path.read_text(encoding="utf-8")
        self._argus_mod = create_argus_namespace(self)

        old_mod = sys.modules.get("argus")
        sys.modules["argus"] = self._argus_mod

        exec_globals = {
            "__builtins__": __builtins__,
            "print": self._argus_mod.api.print,
            "__name__": "__main__",
            "__file__": str(self.file_path),
        }

        try:
            exec(compile(source, str(self.file_path), "exec"), exec_globals)
        finally:
            if old_mod is None:
                sys.modules.pop("argus", None)
            else:
                sys.modules["argus"] = old_mod

        self._lifecycle_callbacks, self._event_callbacks = extract_registered_callbacks(
            self._argus_mod
        )
        self._loaded = True

    def trigger_load(self, ctx: ScriptContext[None]) -> None:
        from backend.core.driver_proxy import DriverProxy
        from backend.interfaces.contexts import ScriptContext as _ScriptContext

        self.load()
        cb = self._lifecycle_callbacks.get("lifecycle.on_load")
        if cb:
            perms = (
                set(self.METADATA.get("permissions", [])) if self.METADATA else set()
            )
            proxy = DriverProxy(getattr(ctx, "driver", None), perms, meta=self.METADATA)
            script_ctx = _ScriptContext[None](
                data=None,
                config=getattr(ctx, "config", None),
                db=getattr(ctx, "db", None),
                driver=proxy,
            )
            cb(script_ctx)

    def trigger_unload(self, ctx: ScriptContext[None]) -> None:
        from backend.core.driver_proxy import DriverProxy
        from backend.interfaces.contexts import ScriptContext as _ScriptContext

        cb = self._lifecycle_callbacks.get("lifecycle.on_unload")
        if cb:
            perms = (
                set(self.METADATA.get("permissions", [])) if self.METADATA else set()
            )
            proxy = DriverProxy(getattr(ctx, "driver", None), perms, meta=self.METADATA)
            script_ctx = _ScriptContext[None](
                data=None,
                config=getattr(ctx, "config", None),
                db=getattr(ctx, "db", None),
                driver=proxy,
            )
            cb(script_ctx)

    def dispatch(self, event_path: str, data: dict[str, object] | None = None) -> None:
        """Dispatch a named event, wrapping data in ScriptContext.

        Respects sleep cooldown (set via ``argus.api.sleep``).
        """
        if data is None:
            data = {}
        cb = self._event_callbacks.get(event_path)
        if cb is None:
            return
        if self._is_asleep:
            return
        from backend.interfaces.contexts import ScriptContext as _ScriptContext

        cb(_ScriptContext(data=data))

    def pop_output(self) -> list[str]:
        if self._argus_mod is None:
            return []
        return self._argus_mod.api.pop_output()

    # ------------------------------------------------------------------
    # Sleep / cooldown
    # ------------------------------------------------------------------

    @property
    def _is_asleep(self) -> bool:
        if self._cooldown_until <= 0:
            return False
        if monotonic_ns() >= self._cooldown_until:
            self._cooldown_until = 0
            return False
        return True

    def _api_sleep(self, ms: int) -> None:
        self._cooldown_until = monotonic_ns() + max(0, ms) * 1_000_000

    # ------------------------------------------------------------------
    # Utilities (mirror LuaScriptWrapper)
    # ------------------------------------------------------------------

    def _api_kill_process(self, pid: int) -> bool:
        if self._driver is None:
            return False
        return self._driver.manage_process(pid, "kill")

    @staticmethod
    def _format_bytes(size: int | float) -> str:
        for unit in ("B", "K", "M", "G", "T", "P"):
            if abs(size) < 1024:
                return f"{size:.1f}{unit}"
            size /= 1024
        return f"{size:.1f}E"

    @staticmethod
    def _format_duration(seconds: float) -> str:
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        if h:
            return f"{h}h {m}m {s}s"
        if m:
            return f"{m}m {s}s"
        return f"{s}s"
