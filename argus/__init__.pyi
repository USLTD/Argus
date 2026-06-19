"""Type stubs for ``import argus`` in Python user scripts.

Usage::

    import argus

    @argus.lifecycle.on_load
    def setup(ctx: argus.PluginContext) -> None:
        argus.api.print("loaded!")

    @argus.events.cpu.on_tick
    def on_cpu(data: dict) -> None:
        argus.api.print(f"CPU: {data['usage_percent']}%")
"""

from types import FunctionType
from typing import Any, Callable, TypeAlias, final

from backend.core.driver_proxy import DriverProxy as _DriverProxy
from backend.interfaces.enums import Permission as _Permission
from backend.interfaces.plugins import PluginMeta as _PluginMeta


# ---------------------------------------------------------------------------
# Context
# ---------------------------------------------------------------------------
@final
class PluginContext:
    """Runtime context passed to lifecycle hooks."""

    config: Any
    db: Any
    driver: _DriverProxy  # DriverProxy instance (permission-gated)


# ---------------------------------------------------------------------------
# Callback slot (``Hook`` is the decorator/assignment type)
# ---------------------------------------------------------------------------
@final
class Hook:
    """
    Supports both ``@decorator`` and ``direct-assignment`` syntax.

    * ``@argus.lifecycle.on_load`` — registers *func* via decorator.
    * ``argus.events.cpu.on_tick = my_func`` — registers by assignment.
    """

    callback: FunctionType | None

    def __call__(self, func: FunctionType) -> FunctionType:
        ...


# ---------------------------------------------------------------------------
# Lifecycle namespace
# ---------------------------------------------------------------------------
@final
class _Lifecycle:
    """``argus.lifecycle`` — script lifecycle events."""

    on_load: Hook
    """Called when the script is loaded (receives :class:`PluginContext`)."""
    on_unload: Hook
    """Called when the script is unloaded (receives :class:`PluginContext`)."""


# ---------------------------------------------------------------------------
# Subsystem event namespaces
# ---------------------------------------------------------------------------
@final
class _GeneralEvents:
    """``argus.events.general`` — general engine events."""

    on_tick: Callable[[dict[str, Any]], None] | Hook
    """Called on each engine tick with the full system state."""

@final
class _CpuEvents:
    """``argus.events.cpu`` — CPU subsystem events."""

    on_tick: Callable[[dict[str, Any]], None] | Hook
    """Called on each tick with ``{usage_percent, physical_cores, logical_cores}``."""

@final
class _MemoryEvents:
    """``argus.events.memory`` — RAM subsystem events."""

    on_tick: Callable[[dict[str, Any]], None] | Hook
    """Called on each tick with ``{percent, total_bytes, used_bytes}``."""

@final
class _DiskEvents:
    """``argus.events.disk`` — Disk subsystem events."""

    on_tick: Callable[[list[dict[str, Any]]], None] | Hook
    """Called on each tick with a list of ``{mount, usage_percent}`` dicts."""

@final
class _NetEvents:
    """``argus.events.net`` — Network subsystem events."""

    on_tick: Callable[[list[dict[str, Any]]], None] | Hook
    """Called on each tick with a list of ``{interface, rx, tx}`` dicts."""

@final
class _ProcessEvents:
    """``argus.events.process`` — Process subsystem events."""

    on_tick: Callable[[list[dict[str, Any]]], None] | Hook
    """Called on each tick with a list of ``{pid, name, cpu_percent}`` dicts."""

@final
class _GpuEvents:
    """``argus.events.gpu`` — GPU subsystem events."""

    on_tick: Callable[[list[dict[str, Any]] | None], None] | Hook
    """Called on each tick with a list of GPU dicts, or ``None``."""

@final
class _BatteryEvents:
    """``argus.events.battery`` — Battery subsystem events."""

    on_tick: Callable[[dict[str, Any] | None], None] | Hook
    """Called on each tick with battery info or ``None``."""

@final
class _SensorEvents:
    """``argus.events.sensor`` — Temperature/voltage sensor events."""

    on_tick: Callable[[list[dict[str, Any]] | None], None] | Hook
    """Called on each tick with a list of sensor dicts, or ``None``."""

@final
class _Events:
    """``argus.events`` — subsystem event callbacks."""

    general: _GeneralEvents
    cpu: _CpuEvents
    memory: _MemoryEvents
    disk: _DiskEvents
    net: _NetEvents
    process: _ProcessEvents
    gpu: _GpuEvents
    battery: _BatteryEvents
    sensor: _SensorEvents


# ---------------------------------------------------------------------------
# API namespace
# ---------------------------------------------------------------------------

@final
class _Api:
    """``argus.api`` — sandbox-safe utility functions."""

    @staticmethod
    def print(*args: Any, **kwargs: Any) -> None:  # pyright: ignore[reportExplicitAny, reportAny]
        """Print (captured to the script's output buffer)."""

    @staticmethod
    def log(*args: Any, **kwargs: Any) -> None:  # pyright: ignore[reportExplicitAny, reportAny]
        """Alias for :func:`print`."""

    @staticmethod
    def sleep(ms: int) -> None:
        """Suspend callback execution for *ms* milliseconds."""

    @staticmethod
    def timestamp() -> float:
        """Return the current Unix timestamp."""

    @staticmethod
    def format_bytes(size: int | float) -> str:
        """Format *size* bytes into a human-readable string (e.g. ``"1.5G"``)."""

    @staticmethod
    def format_duration(seconds: float) -> str:
        """Format *seconds* into a human-readable string (e.g. ``"2m 30s"``)."""

    @staticmethod
    def kill_process(pid: int) -> bool:
        """Kill the process identified by *pid*. Returns ``True`` on success."""


# ---------------------------------------------------------------------------
# Script namespace
# ---------------------------------------------------------------------------

@final
class _Script:
    """``argus.script`` — permission and script utilities."""

    Permission = _Permission
    Metadata = _PluginMeta


# ---------------------------------------------------------------------------
# Module-level attributes (injected by PythonScriptWrapper)
# ---------------------------------------------------------------------------

lifecycle: TypeAlias = _Lifecycle
events: TypeAlias = _Events
api: TypeAlias = _Api
script: TypeAlias = _Script