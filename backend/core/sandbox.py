"""
Lua script sandbox with two-phase loading.

Phase 1 — Extract METADATA and evaluate compatibility (no sandbox).
Phase 2 — Full sandbox with restricted globals (only if compatible).
"""

from pathlib import Path
from typing import Any, Optional

from lupa import LuaRuntime

from backend.interfaces.enums import CompatAction, Permission
from backend.interfaces.plugins import BaseDriver, BaseUserScript, PluginMeta

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

    def __init__(self, file_path: Path, source: str, meta: PluginMeta) -> None:
        self.file_path = file_path
        self.METADATA = meta
        self._hooks: dict[str, Any] = {}
        self._events: dict[str, Any] = {}
        self._output_buffer: list[str] = []
        self._driver: BaseDriver | None = None

        # Phase 2 — full sandbox
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        g = self.lua.globals()

        g["argus"] = self.lua.table_from(
            {
                "hooks": self.lua.table_from({}),
                "events": self.lua.table_from({}),
                "api": self.lua.table_from({}),
            }
        )

        self.lua.execute(source)

        self._sandbox_globals(g)
        self._install_argus_api(g)
        g["print"] = g["argus"]["api"]["print"]
        self._capture_hooks_and_events(g)

    # ------------------------------------------------------------------
    # Factory — Phase 1 + Phase 2
    # ------------------------------------------------------------------

    @classmethod
    def create_if_compatible(
        cls,
        file_path: Path,
        compat_ctx: Any,
        config: Any,
    ) -> Optional["LuaScriptWrapper"]:
        """Phase 1: extract METADATA, evaluate compatibility.
        Phase 2: build full sandbox (if compatible)."""
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()

        # Phase 1 — bare runtime, stub argus, no sandbox
        phase1 = LuaRuntime(unpack_returned_tuples=True)
        g1 = phase1.globals()
        g1["argus"] = phase1.table_from(
            {
                "hooks": phase1.table_from({}),
                "events": phase1.table_from({}),
                "api": phase1.table_from({}),
            }
        )
        phase1.execute(source)
        meta = cls._parse_metadata(g1, file_path)

        # Evaluate compatibility
        compatible = cls._evaluate_compatible(meta, compat_ctx, config)
        if not compatible:
            return None

        # Phase 2 — pass source to avoid re-reading
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
        compat_ctx: Any,
        config: Any,
    ) -> bool:
        from backend.interfaces.rules import evaluate_script_compatible

        compatible_rules = meta.get("compatible")
        result = evaluate_script_compatible(compatible_rules, compat_ctx)
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

    def _install_argus_api(self, g: Any) -> None:
        perms = set(self.METADATA.get("permissions", []))
        api_tbl = g["argus"]["api"]

        api_tbl["print"] = self._capture_print

        if Permission.PROCESS_KILL in perms:
            api_tbl["kill_process"] = self._api_kill_process
        else:
            api_tbl["kill_process"] = self._make_blocked("PROCESS.KILL")

    def _api_kill_process(self, pid: int) -> bool:
        if self._driver is None:
            return False
        return self._driver.manage_process(pid, "kill")

    def _make_blocked(self, perm: str):
        msg = self._BLOCKED_MSG.format(perm=perm)

        def blocked(*args: Any, **kwargs: Any) -> bool:
            print(msg)
            return False

        return blocked

    # ------------------------------------------------------------------
    # Capture hooks and events
    # ------------------------------------------------------------------

    def _capture_hooks_and_events(self, g: Any) -> None:
        try:
            argus_tbl = g["argus"]
        except KeyError, TypeError:
            return
        if not argus_tbl:
            return

        try:
            hooks_tbl = argus_tbl["hooks"]
        except KeyError, TypeError:
            hooks_tbl = None
        if hooks_tbl:
            try:
                on_load = hooks_tbl["on_load"]
            except KeyError, TypeError:
                on_load = None
            if on_load:
                self._hooks["on_load"] = on_load
            try:
                on_unload = hooks_tbl["on_unload"]
            except KeyError, TypeError:
                on_unload = None
            if on_unload:
                self._hooks["on_unload"] = on_unload

        try:
            events_tbl = argus_tbl["events"]
        except KeyError, TypeError:
            events_tbl = None
        if events_tbl:
            try:
                on_tick = events_tbl["on_tick"]
            except KeyError, TypeError:
                on_tick = None
            if on_tick:
                self._events["on_tick"] = on_tick

    # ------------------------------------------------------------------
    # Driver binding
    # ------------------------------------------------------------------

    def bind_driver(self, driver: BaseDriver | None) -> None:
        self._driver = driver

    # ------------------------------------------------------------------
    # Plugin interface
    # ------------------------------------------------------------------

    def execute_tick(self, system_state: dict[str, Any]) -> None:
        on_tick = self._events.get("on_tick")
        if on_tick:
            on_tick(self.lua.table_from(system_state))

    def trigger_load(self, ctx: Any) -> None:
        on_load = self._hooks.get("on_load")
        if on_load:
            on_load(
                self.lua.table_from(
                    {"config": ctx.config, "db": ctx.db, "driver": ctx.driver}
                )
            )

    def trigger_unload(self, ctx: Any) -> None:
        on_unload = self._hooks.get("on_unload")
        if on_unload:
            on_unload(
                self.lua.table_from(
                    {"config": ctx.config, "db": ctx.db, "driver": ctx.driver}
                )
            )
