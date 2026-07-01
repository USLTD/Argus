"""Type stubs for ``import argus`` in Python user scripts.

Usage::

    import argus

    @argus.lifecycle.on_load
    def setup(ctx: argus.ScriptContext[None]) -> None:
        argus.api.print("loaded!")

    @argus.events.cpu.on_tick
    def on_cpu(ctx: argus.ScriptContext[dict]) -> None:
        data = ctx.data
        argus.api.print(f"CPU: {data['usage_percent']}%")
"""

from typing import Any, Callable, TypeAlias, final

from backend.interfaces.contexts import (
    GeneralTickData,
    CpuTickData,
    MemoryTickData,
    DiskTickData,
    NetworkTickData,
    ProcessTickData,
    GpuTickData,
    BatteryTickData,
    SensorTickData,
    UserTickData,
)
from backend.interfaces.sentinels import Unavailable
from backend.interfaces.enums import Permission as _Permission
from backend.interfaces.plugins import PluginMeta as _PluginMeta
from ._common import Hook, ScriptContext


# ---------------------------------------------------------------------------
# Lifecycle namespace
# ---------------------------------------------------------------------------
@final
class _Lifecycle:
    """``argus.lifecycle`` — script lifecycle events."""

    on_load: Hook
    """Called when the script is loaded (receives :class:`ScriptContext[None]`)."""
    on_unload: Hook
    """Called when the script is unloaded (receives :class:`ScriptContext[None]`)."""


# ---------------------------------------------------------------------------
# Subsystem event namespaces
# ---------------------------------------------------------------------------
@final
class _GeneralEvents:
    """``argus.events.general`` — general engine events."""

    on_tick: Callable[[ScriptContext[GeneralTickData]], None] | Hook
    """Called on each engine tick with the full system state in ``ctx.data``."""

@final
class _CpuEvents:
    """``argus.events.cpu`` — CPU subsystem events."""

    on_tick: Callable[[ScriptContext[CpuTickData]], None] | Hook
    """Called on each tick; ``ctx.data`` contains ``{usage_percent, physical_cores, logical_cores}``."""

@final
class _MemoryEvents:
    """``argus.events.memory`` — RAM subsystem events."""

    on_tick: Callable[[ScriptContext[MemoryTickData]], None] | Hook
    """Called on each tick; ``ctx.data`` contains ``{percent, total_bytes, used_bytes}``."""

@final
class _DiskEvents:
    """``argus.events.disk`` — Disk subsystem events."""

    on_tick: Callable[[ScriptContext[list[DiskTickData]]], None] | Hook
    """Called on each tick; ``ctx.data`` is a list of ``{mount, usage_percent}`` dicts."""

@final
class _NetEvents:
    """``argus.events.net`` — Network subsystem events."""

    on_tick: Callable[[ScriptContext[list[NetworkTickData]]], None] | Hook
    """Called on each tick; ``ctx.data`` is a list of ``{interface, rx, tx}`` dicts."""

@final
class _ProcessEvents:
    """``argus.events.process`` — Process subsystem events."""

    on_tick: Callable[[ScriptContext[list[ProcessTickData]]], None] | Hook
    """Called on each tick; ``ctx.data`` is a list of ``{pid, name, cpu_percent}`` dicts."""

@final
class _GpuEvents:
    """``argus.events.gpu`` — GPU subsystem events."""

    on_tick: Callable[[ScriptContext[GpuTickData | None]], None] | Hook
    """Called on each tick; ``ctx.data`` is a list of GPU dicts, or ``None``."""

@final
class _BatteryEvents:
    """``argus.events.battery`` — Battery subsystem events."""

    on_tick: Callable[[ScriptContext[BatteryTickData | None]], None] | Hook
    """Called on each tick; ``ctx.data`` contains battery info or ``None``."""

@final
class _SensorEvents:
    """``argus.events.sensor`` — Temperature/voltage sensor events."""

    on_tick: Callable[[ScriptContext[list[SensorTickData] | None]], None] | Hook
    """Called on each tick; ``ctx.data`` is a list of sensor dicts, or ``None``."""

@final
class _UsersEvents:
    """``argus.events.users`` — User session events."""

    on_tick: Callable[[ScriptContext[list[UserTickData] | None]], None] | Hook
    """Called on each tick; ``ctx.data`` is a list of user dicts, or ``None``."""

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
    users: _UsersEvents


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

