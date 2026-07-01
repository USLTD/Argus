"""
Lua script sandbox with injector-driven two-phase loading.

Phase 1 — Extract METADATA and evaluate compatibility (no sandbox).
Phase 2 — Full sandbox with injector-driven namespaces (only if compatible).
"""

from __future__ import annotations

from pathlib import Path
from time import monotonic_ns
from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING, Any

from lupa import LuaRuntime

from backend.core.injectors import HookInjector, all_injectors, init_injectors
from backend.interfaces.enums import CompatAction, Permission, ScriptExecutionMode
from backend.interfaces.plugins import BaseDriver, BaseUserScript, PluginMeta

if TYPE_CHECKING:
    from backend.interfaces.contexts import ScriptContext
    from backend.interfaces.rules import CompatContext
    from backend.storage.config import ArgusConfig

_INJECTED_GLOBALS = (
    "collectgarbage",
    "coroutine",
    "debug",
    "dofile",
    "io",
    "load",
    "loadfile",
    "os",
    "package",
    "rawequal",
    "rawget",
    "rawset",
    "require",
)

_DANGEROUS_GLOBALS = (
    "os",
    "io",
    "dofile",
    "loadfile",
    "require",
    "load",
    "rawget",
    "rawset",
    "rawequal",
    "getmetatable",
    "setmetatable",
)


class IncompatibleScriptError(Exception):
    """Raised when a Lua script is found to be incompatible during Phase 1."""


class LuaScriptWrapper(BaseUserScript):
    """A loaded, sandboxed, compatible Lua user script.

    Do **not** construct directly — use :meth:`create_if_compatible` instead.
    """

    _BLOCKED_MSG = (
        "[Sandbox] Permission denied: '{perm}' is not declared in METADATA.permissions"
    )

    def __init__(
        self,
        file_path: Path,
        source: str,
        meta: PluginMeta,
        execution_mode: ScriptExecutionMode = ScriptExecutionMode.NONBLOCKING,
    ) -> None:
        self.file_path = file_path
        self.METADATA = meta
        self.execution_mode = execution_mode
        self._callbacks: dict[str, Any] = {}
        self._output_buffer: list[str] = []
        self._driver: BaseDriver | None = None
        self._cooldown_until: int = 0

        perms = set(meta.get("permissions", []))

        self.lua = LuaRuntime(unpack_returned_tuples=True)
        g = self.lua.globals()

        argus_tbl = self.lua.table_from(
            {
                "lifecycle": self.lua.table_from({}),
                "events": self.lua.table_from({}),
                "api": self.lua.table_from({}),
            }
        )
        g["argus"] = argus_tbl

        # Phase 2a — inject stubs (create deeper namespace tables)
        for inj in self._all_injectors():
            inj.inject_stub(self.lua, argus_tbl)

        # Phase 2b — execute script (script fills in callbacks + uses APIs)
        self.lua.execute(source)

        # Phase 2c — sandbox dangerous globals
        self._sandbox_globals(g)

        # Phase 2d — capture callbacks and install APIs via injectors
        for inj in self._all_injectors():
            captured = inj.capture_or_install(self.lua, argus_tbl, self, perms)
            self._callbacks.update(captured)

        # Phase 2e — wire print alias to argus.api.print
        g["print"] = g["argus"]["api"]["print"]

    # ------------------------------------------------------------------
    # Introspection properties
    # ------------------------------------------------------------------

    @property
    def hooked_events(self) -> list[str]:
        """Event paths this script has registered callbacks for."""
        return list(self._callbacks.keys())

    @property
    def script_type(self) -> str:
        """Returns ``\"lua\"`` — used by list_scripts() to identify the language."""
        return "lua"

    # ------------------------------------------------------------------
    # Injector helper
    # ------------------------------------------------------------------

    @staticmethod
    def _all_injectors() -> list[HookInjector]:
        init_injectors()
        return all_injectors()

    # ------------------------------------------------------------------
    # Factory — Phase 1 + Phase 2
    # ------------------------------------------------------------------

    @classmethod
    def create_if_compatible(
        cls,
        file_path: Path,
        compat_ctx: CompatContext,
        config: ArgusConfig,
    ) -> LuaScriptWrapper | None:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()

        # Phase 1 — bare runtime, stub argus, no sandbox
        phase1 = LuaRuntime(unpack_returned_tuples=True)
        g1 = phase1.globals()
        argus1 = phase1.table_from(
            {
                "lifecycle": phase1.table_from({}),
                "events": phase1.table_from({}),
                "api": phase1.table_from({}),
            }
        )
        g1["argus"] = argus1
        for inj in cls._all_injectors():
            inj.inject_stub(phase1, argus1)
        phase1.execute(source)
        meta = cls._parse_metadata(g1, file_path)

        # Evaluate compatibility
        compatible = cls._evaluate_compatible(meta, compat_ctx, config)
        if not compatible:
            return None

        return cls(file_path, source, meta)

    # ------------------------------------------------------------------
    # METADATA parsing
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_metadata(g: Any, file_path: Path) -> PluginMeta:
        try:
            lua_meta = g["METADATA"]
        except KeyError, TypeError:
            lua_meta = None
        if not lua_meta:
            return {
                "name": file_path.stem,
                "author": "Unknown",
                "version": "1.0",
                "permissions": [],
            }

        try:
            raw_perms = (
                list(lua_meta.permissions.values()) if lua_meta.permissions else []
            )
        except Exception:
            raw_perms = []
        try:
            perm_objects = [Permission(p) for p in raw_perms]
        except ValueError as e:
            msg = f"Invalid permission in {file_path.name}: {e}"
            raise ValueError(msg) from e

        meta: PluginMeta = {
            "name": str(getattr(lua_meta, "name", None) or file_path.stem),
            "author": str(getattr(lua_meta, "author", None) or "Unknown"),
            "version": str(getattr(lua_meta, "version", None) or "1.0"),
            "permissions": perm_objects,
        }

        raw_compat = getattr(lua_meta, "compatible", None)
        if raw_compat:
            rules: list[str] = []
            try:
                for v in raw_compat.values():
                    rules.append(str(v))
            except Exception:
                pass
            if rules:
                meta["compatible"] = rules

        return meta

    # ------------------------------------------------------------------
    # Compatibility evaluation
    # ------------------------------------------------------------------

    @staticmethod
    def _evaluate_compatible(
        meta: PluginMeta,
        compat_ctx: CompatContext,
        config: ArgusConfig,
    ) -> bool:
        from backend.interfaces.rules import evaluate_script_compatible

        compatible_rules = meta.get("compatible")
        # Lua scripts only use list[str] compat (callable is for drivers)
        result = evaluate_script_compatible(
            compatible_rules if isinstance(compatible_rules, list) else None,
            compat_ctx,
        )
        if result is not None:
            return result
        return config.script_compatibility_default == CompatAction.LOAD

    # ------------------------------------------------------------------
    # Sandboxing
    # ------------------------------------------------------------------

    def _sandbox_globals(self, g: Any) -> None:
        for name in _INJECTED_GLOBALS:
            try:
                g[name] = None
            except Exception:
                pass

    def _capture_print(self, *args: Any) -> None:
        msg = " ".join(str(a) for a in args)
        self._output_buffer.append(msg)

    def pop_output(self) -> list[str]:
        out = list(self._output_buffer)
        self._output_buffer.clear()
        return out

    # ------------------------------------------------------------------
    # argus.api — sandbox-safe functions
    # ------------------------------------------------------------------

    def _api_sleep(self, ms: int) -> None:
        self._cooldown_until = monotonic_ns() + max(0, ms) * 1_000_000

    def _api_kill_process(self, pid: int) -> bool:
        if self._driver is None:
            return False
        return self._driver.manage_process(pid, "kill")

    def _make_blocked(self, perm: str) -> Callable[..., bool]:
        msg = self._BLOCKED_MSG.format(perm=perm)

        def blocked(*args: Any, **kwargs: Any) -> bool:
            print(msg)
            return False

        return blocked

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

    # ------------------------------------------------------------------
    # Event dispatch
    # ------------------------------------------------------------------

    def dispatch(
        self, event_path: str, data: Mapping[str, object] | None = None
    ) -> None:
        """Dispatch a named event to the matching Lua callback.

        Wraps *data* in a Lua table with the same shape as ScriptContext,
        so Lua callbacks receive ``ctx.data``.
        Respects sleep cooldown (set via ``argus.api.sleep``).
        """
        if data is None:
            data = {}
        cb = self._callbacks.get(event_path)
        if cb is None:
            return
        if self._is_asleep:
            return
        lua_ctx = self.lua.table_from(
            {
                "data": self.lua.table_from(data),
                "config": None,
                "db": None,
                "driver": None,
            }
        )
        cb(lua_ctx)

    @property
    def _is_asleep(self) -> bool:
        if self._cooldown_until <= 0:
            return False
        if monotonic_ns() >= self._cooldown_until:
            self._cooldown_until = 0
            return False
        return True

    # ------------------------------------------------------------------
    # Backward-compat aliases
    # ------------------------------------------------------------------

    def bind_driver(self, driver: BaseDriver | None) -> None:
        self._driver = driver

    def execute_tick(self, system_state: Mapping[str, object]) -> None:
        """Alias — dispatches ``events.general.on_tick``."""
        self.dispatch("events.general.on_tick", system_state)

    def trigger_load(self, ctx: ScriptContext[None]) -> None:
        from backend.core.driver_proxy import DriverProxy

        perms = set(self.METADATA.get("permissions", [])) if self.METADATA else set()
        proxy = DriverProxy(self._driver, perms, meta=self.METADATA)
        self.dispatch(
            "lifecycle.on_load",
            {
                "config": getattr(ctx, "config", None),
                "db": getattr(ctx, "db", None),
                "driver": proxy,
            },
        )

    def trigger_unload(self, ctx: ScriptContext[None]) -> None:
        from backend.core.driver_proxy import DriverProxy

        perms = set(self.METADATA.get("permissions", [])) if self.METADATA else set()
        proxy = DriverProxy(self._driver, perms, meta=self.METADATA)
        self.dispatch(
            "lifecycle.on_unload",
            {
                "config": getattr(ctx, "config", None),
                "db": getattr(ctx, "db", None),
                "driver": proxy,
            },
        )
