"""
Injector framework for the Lua sandbox.

Each injector is responsible for a namespace under ``argus``:

* **EventInjector** — creates stub tables and captures Lua callbacks after
  script execution. Yields entries in the callback dict keyed by dotted event
  path (e.g. ``"events.cpu.on_tick"``).
* **ApiInjector** — creates stub tables and installs Python API functions.
  Returns an empty callback dict.

Registry
--------
Use ``init_injectors()`` once at startup (lazy, idempotent).
Use ``reset_injectors()`` between tests.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, final, override

from lupa import LuaRuntime

from backend.interfaces.enums import Permission


class HookInjector(ABC):
    """Create namespace tables under ``argus`` and either capture callbacks
    or install API functions."""

    namespace_path: str
    permission: Permission | None
    name: str

    @abstractmethod
    def inject_stub(self, lua: LuaRuntime, argus_tbl: Any) -> None:
        """Phase 1: build the namespace chain of empty Lua tables under
        *argus_tbl* so scripts can assign into them before we sandbox."""

    @abstractmethod
    def capture_or_install(
        self,
        lua: LuaRuntime,
        argus_tbl: Any,
        wrapper: Any,
        perms: set[Permission],
    ) -> dict[str, Any]:
        """Phase 2: after script execution.

        * For event injectors — walk the namespace, find callable entries,
          return ``{"events.cpu.on_tick": <lua function>}``.
        * For API injectors — install Python functions, return ``{}``.
        """


@final
class EventInjector(HookInjector):
    """Injects a namespace subtree and captures Lua callbacks."""

    def __init__(
        self,
        namespace_path: str,
        events: list[str],
        permission: Permission | None = None,
    ) -> None:
        self.namespace_path = namespace_path
        self.events = events
        self.permission = permission
        self.name = namespace_path.replace(".", "_")

    @override
    def inject_stub(self, lua: LuaRuntime, argus_tbl: Any) -> None:
        parts = self.namespace_path.split(".")
        current = argus_tbl
        for part in parts:
            child = current[part]
            if child is None:
                child = lua.table_from({})
                current[part] = child
            current = child

    @override
    def capture_or_install(
        self,
        lua: LuaRuntime,
        argus_tbl: Any,
        wrapper: Any,
        perms: set[Permission],
    ) -> dict[str, Any]:
        if self.permission is not None and self.permission not in perms:
            return {}

        parts = self.namespace_path.split(".")
        current: Any = argus_tbl
        for part in parts:
            current = current[part]
            if current is None:
                return {}

        callbacks: dict[str, Any] = {}
        for event in self.events:
            cb = current[event]
            if cb is not None:
                callbacks[f"{self.namespace_path}.{event}"] = cb
        return callbacks


@final
class ApiInjector(HookInjector):
    """Installs Python API functions into a namespace under ``argus``.

    Returns an empty callback dict.
    """

    def __init__(self, namespace_path: str = "api") -> None:
        self.namespace_path = namespace_path
        self.permission: Permission | None = None
        self.name = namespace_path

    @override
    def inject_stub(self, lua: LuaRuntime, argus_tbl: Any) -> None:
        parts = self.namespace_path.split(".")
        current = argus_tbl
        for part in parts:
            child = current[part]
            if child is None:
                child = lua.table_from({})
                current[part] = child
            current = child

    @override
    def capture_or_install(
        self,
        lua: LuaRuntime,
        argus_tbl: Any,
        wrapper: Any,
        perms: set[Permission],
    ) -> dict[str, Any]:
        import time as _time

        parts = self.namespace_path.split(".")
        current: Any = argus_tbl
        for part in parts:
            current = current[part]
            if current is None:
                return {}

        current["print"] = wrapper._capture_print
        current["log"] = wrapper._capture_print
        current["sleep"] = wrapper._api_sleep
        current["timestamp"] = _time.time
        current["format_bytes"] = wrapper._format_bytes
        current["format_duration"] = wrapper._format_duration

        if Permission.PROCESSES_EXECUTE in perms:
            current["kill_process"] = wrapper._api_kill_process
        else:
            current["kill_process"] = wrapper._make_blocked("PROCESSES.EXECUTE")

        return {}


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_INJECTORS: list[HookInjector] = []
_INJECTORS_INITIALIZED = False


def register(injector: HookInjector) -> None:
    _INJECTORS.append(injector)


def all_injectors() -> list[HookInjector]:
    return list(_INJECTORS)


def reset_injectors() -> None:
    global _INJECTORS_INITIALIZED
    _INJECTORS.clear()
    _INJECTORS_INITIALIZED = False  # pyright: ignore[reportConstantRedefinition]


def init_injectors() -> None:
    global _INJECTORS_INITIALIZED
    if _INJECTORS_INITIALIZED:
        return
    _INJECTORS_INITIALIZED = True  # pyright: ignore[reportConstantRedefinition]

    from backend.core.injectors.hooks import get_hooks_injector
    from backend.core.injectors.events import get_events_injectors
    from backend.core.injectors.api import get_api_injector

    register(get_hooks_injector())
    for inj in get_events_injectors():
        register(inj)
    register(get_api_injector())
