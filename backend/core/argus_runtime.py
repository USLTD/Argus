"""
argus_runtime — Per-script ``argus`` namespace for Python user scripts.

Every :class:`PythonScriptWrapper` gets its own isolated ``argus`` module
so that callbacks registered by one script never leak into another.
Script authors write::

    import argus

    @argus.lifecycle.on_load
    def setup(ctx):
        print("loaded!")

    def on_cpu(data):
        print(f"CPU: {data['usage_percent']}%")

    argus.events.cpu.on_tick = on_cpu

Supports **both** decorator and direct-assignment syntax on every slot.
"""

from __future__ import annotations

from types import ModuleType
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Generic, TypeVar

if TYPE_CHECKING:
    from backend.core.python_script import PythonScriptWrapper

from backend.interfaces.contexts import (
    GeneralTickData, CpuTickData, MemoryTickData,
    DiskTickData, NetworkTickData, ProcessTickData,
    GpuTickData, BatteryTickData, SensorTickData, ScriptContext,
)
from backend.interfaces.enums import Permission


T = TypeVar("T", bound=Callable[..., object])


# ---------------------------------------------------------------------------
# Callback slot
# ---------------------------------------------------------------------------

class CallbackSlot(Generic[T]):
    """A slot that supports **both** decorator and assignment registration.

    * ``@slot`` — ``CallbackSlot.__call__(func)`` stores and returns *func*.
    * ``slot = func`` — replaces the entire slot (the wrapper detects a
      plain callable as a direct-registered callback).

    The wrapper always checks both paths::

        if isinstance(slot, CallbackSlot):   # decorator path
            cb = slot.callback
        elif callable(slot):                 # assignment path
            cb = slot
    """

    def __init__(self) -> None:
        self._callback: T | None = None

    def __call__(self, func: T) -> T:
        self._callback = func
        return func

    @property
    def callback(self) -> T | None:
        return self._callback


# ---------------------------------------------------------------------------
# Lifecycle namespace  (argus.lifecycle.*)
# ---------------------------------------------------------------------------

class LifecycleNamespace:
    """``argus.lifecycle`` — script lifecycle events."""

    on_load: CallbackSlot[Callable[[ScriptContext[None]], None]]
    on_unload: CallbackSlot[Callable[[ScriptContext[None]], None]]

    def __init__(self) -> None:
        self.on_load = CallbackSlot[Callable[[ScriptContext[None]], None]]()
        self.on_unload = CallbackSlot[Callable[[ScriptContext[None]], None]]()


# ---------------------------------------------------------------------------
# Events namespace  (argus.events.<subsystem>.<event>)
# ---------------------------------------------------------------------------

class GeneralEvents:
    on_tick: CallbackSlot[Callable[[ScriptContext[GeneralTickData]], None]]
    def __init__(self) -> None:
        self.on_tick = CallbackSlot[Callable[[ScriptContext[GeneralTickData]], None]]()

class CpuEvents:
    on_tick: CallbackSlot[Callable[[ScriptContext[CpuTickData]], None]]
    def __init__(self) -> None:
        self.on_tick = CallbackSlot[Callable[[ScriptContext[CpuTickData]], None]]()

class MemoryEvents:
    on_tick: CallbackSlot[Callable[[ScriptContext[MemoryTickData]], None]]
    def __init__(self) -> None:
        self.on_tick = CallbackSlot[Callable[[ScriptContext[MemoryTickData]], None]]()

class DiskEvents:
    on_tick: CallbackSlot[Callable[[ScriptContext[list[DiskTickData]]], None]]
    on_read: CallbackSlot[Callable[[ScriptContext[DiskTickData]], None]]
    on_write: CallbackSlot[Callable[[ScriptContext[DiskTickData]], None]]
    def __init__(self) -> None:
        self.on_tick = CallbackSlot[Callable[[ScriptContext[list[DiskTickData]]], None]]()
        self.on_read = CallbackSlot[Callable[[ScriptContext[DiskTickData]], None]]()
        self.on_write = CallbackSlot[Callable[[ScriptContext[DiskTickData]], None]]()

class NetEvents:
    on_tick: CallbackSlot[Callable[[ScriptContext[list[NetworkTickData]]], None]]
    on_rx: CallbackSlot[Callable[[ScriptContext[NetworkTickData]], None]]
    on_tx: CallbackSlot[Callable[[ScriptContext[NetworkTickData]], None]]
    def __init__(self) -> None:
        self.on_tick = CallbackSlot[Callable[[ScriptContext[list[NetworkTickData]]], None]]()
        self.on_rx = CallbackSlot[Callable[[ScriptContext[NetworkTickData]], None]]()
        self.on_tx = CallbackSlot[Callable[[ScriptContext[NetworkTickData]], None]]()

class ProcessEvents:
    on_tick: CallbackSlot[Callable[[ScriptContext[list[ProcessTickData]]], None]]
    on_spawn: CallbackSlot[Callable[[ScriptContext[ProcessTickData]], None]]
    on_exit: CallbackSlot[Callable[[ScriptContext[ProcessTickData]], None]]
    def __init__(self) -> None:
        self.on_tick = CallbackSlot[Callable[[ScriptContext[list[ProcessTickData]]], None]]()
        self.on_spawn = CallbackSlot[Callable[[ScriptContext[ProcessTickData]], None]]()
        self.on_exit = CallbackSlot[Callable[[ScriptContext[ProcessTickData]], None]]()

class GpuEvents:
    on_tick: CallbackSlot[Callable[[ScriptContext[GpuTickData | None]], None]]
    def __init__(self) -> None:
        self.on_tick = CallbackSlot[Callable[[ScriptContext[GpuTickData | None]], None]]()

class BatteryEvents:
    on_tick: CallbackSlot[Callable[[ScriptContext[BatteryTickData | None]], None]]
    def __init__(self) -> None:
        self.on_tick = CallbackSlot[Callable[[ScriptContext[BatteryTickData | None]], None]]()

class SensorEvents:
    on_tick: CallbackSlot[Callable[[ScriptContext[list[SensorTickData] | None]], None]]
    def __init__(self) -> None:
        self.on_tick = CallbackSlot[Callable[[ScriptContext[list[SensorTickData] | None]], None]]()

class EventsNamespace:
    """``argus.events`` — subsystem event callbacks."""

    general: GeneralEvents
    cpu: CpuEvents
    memory: MemoryEvents
    disk: DiskEvents
    net: NetEvents
    process: ProcessEvents
    gpu: GpuEvents
    battery: BatteryEvents
    sensor: SensorEvents

    def __init__(self) -> None:
        self.general = GeneralEvents()
        self.cpu = CpuEvents()
        self.memory = MemoryEvents()
        self.disk = DiskEvents()
        self.net = NetEvents()
        self.process = ProcessEvents()
        self.gpu = GpuEvents()
        self.battery = BatteryEvents()
        self.sensor = SensorEvents()


# ---------------------------------------------------------------------------
# API namespace  (argus.api.*)
# ---------------------------------------------------------------------------

class ApiNamespace:
    """``argus.api`` — sandbox-safe utility functions."""

    def __init__(self, wrapper: PythonScriptWrapper) -> None:
        self._wrapper = wrapper
        self._buffer: list[str] = []

    # -- print / log (captured output) -----------------------------------

    def print(self, *args: Any, **kwargs: Any) -> None:
        """Capture ``print()`` output to the script's output buffer."""
        msg = " ".join(str(a) for a in args)
        self._buffer.append(msg)

    def log(self, *args: Any, **kwargs: Any) -> None:
        """Alias for :meth:`print`."""
        self.print(*args, **kwargs)

    def pop_output(self) -> list[str]:
        """Return and clear the captured output buffer."""
        out = list(self._buffer)
        self._buffer.clear()
        return out

    # -- utilities (delegate to wrapper) ---------------------------------

    def sleep(self, ms: int) -> None:
        self._wrapper._api_sleep(ms)

    def timestamp(self) -> float:
        import time
        return time.time()

    def format_bytes(self, size: int | float) -> str:
        return self._wrapper._format_bytes(size)

    def format_duration(self, seconds: float) -> str:
        return self._wrapper._format_duration(seconds)

    def kill_process(self, pid: int) -> bool:
        return self._wrapper._api_kill_process(pid)


# ---------------------------------------------------------------------------
# Script namespace  (argus.script.*)
# ---------------------------------------------------------------------------

class ScriptNamespace:
    """``argus.script`` — permission and script utilities."""

    Permission = Permission


class TypesNamespace:
    """``argus.types`` — context type aliases for script callbacks.

    These mirror the stub aliases in ``argus/types.pyi`` so that
    ``from argus.types import CpuCtx`` works at runtime without error.
    The actual type inference comes from the ``.pyi`` stub.
    """

    CpuCtx: type = ScriptContext  # type: ignore[valid-type]
    MemCtx: type = ScriptContext  # type: ignore[valid-type]
    DiskCtx: type = ScriptContext  # type: ignore[valid-type]
    NetCtx: type = ScriptContext  # type: ignore[valid-type]
    ProcCtx: type = ScriptContext  # type: ignore[valid-type]
    GpuCtx: type = ScriptContext  # type: ignore[valid-type]
    BatCtx: type = ScriptContext  # type: ignore[valid-type]
    SensorCtx: type = ScriptContext  # type: ignore[valid-type]
    GeneralCtx: type = ScriptContext  # type: ignore[valid-type]
    LifecycleCtx: type = ScriptContext  # type: ignore[valid-type]


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def create_argus_namespace(wrapper: PythonScriptWrapper) -> ModuleType:
    """Create a fresh ``argus`` module namespace for a single script.

    Every call returns an independent instance so scripts are isolated.
    """
    mod = ModuleType("argus")
    mod.lifecycle = LifecycleNamespace()  # type: ignore[attr-defined]
    mod.events = EventsNamespace()  # type: ignore[attr-defined]
    mod.api = ApiNamespace(wrapper)  # type: ignore[attr-defined]
    mod.script = ScriptNamespace()  # type: ignore[attr-defined]
    mod.types = TypesNamespace()  # type: ignore[attr-defined]
    return mod


# ---------------------------------------------------------------------------
# Callback extraction (after script exec)
# ---------------------------------------------------------------------------

# Subsystem→event-name mapping for callback extraction.
# Mirrors the event classes defined above.
_SUBSYSTEM_EVENT_NAMES: dict[str, list[str]] = {
    "general": ["on_tick"],
    "cpu": ["on_tick"],
    "memory": ["on_tick"],
    "disk": ["on_tick", "on_read", "on_write"],
    "net": ["on_tick", "on_rx", "on_tx"],
    "process": ["on_tick", "on_spawn", "on_exit"],
    "gpu": ["on_tick"],
    "battery": ["on_tick"],
    "sensor": ["on_tick"],
}


def extract_registered_callbacks(
    argus_mod: ModuleType,
) -> tuple[dict[str, Callable[..., object]], dict[str, Callable[..., object]]]:
    """Walk the namespace and collect registered lifecycle & event callbacks.

    Returns ``(lifecycle_callbacks, event_callbacks)`` where keys are dotted
    paths like ``"lifecycle.on_load"`` and ``"events.cpu.on_tick"``.

    Handles both decorator-registered (``CallbackSlot``) and direct-assignment
    (plain callable) slots.
    """
    lifecycle: dict[str, Callable[..., object]] = {}
    events: dict[str, Callable[..., object]] = {}

    # -- Lifecycle --
    for name in ("on_load", "on_unload", "on_reload"):
        slot = getattr(argus_mod.lifecycle, name, None)
        cb = _resolve_callback(slot)
        if cb is not None:
            lifecycle[f"lifecycle.{name}"] = cb

    # -- Events --
    for sub_name, event_names in _SUBSYSTEM_EVENT_NAMES.items():
        subsystem = getattr(argus_mod.events, sub_name, None)
        if subsystem is None:
            continue
        for evt_name in event_names:
            slot = getattr(subsystem, evt_name, None)
            cb = _resolve_callback(slot)
            if cb is not None:
                events[f"events.{sub_name}.{evt_name}"] = cb

    return lifecycle, events


def _resolve_callback(slot: object) -> Callable[..., object] | None:
    """Unify decorator and assignment paths into a single callback."""
    if isinstance(slot, CallbackSlot):
        return slot.callback
    if callable(slot):
        return slot
    return None
