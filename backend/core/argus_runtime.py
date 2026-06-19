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
from typing import Any

from backend.interfaces.enums import Permission


# ---------------------------------------------------------------------------
# Callback slot
# ---------------------------------------------------------------------------

class CallbackSlot:
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
        self._callback: Callable | None = None

    def __call__(self, func: Callable) -> Callable:
        self._callback = func
        return func

    @property
    def callback(self) -> Callable | None:
        return self._callback


# ---------------------------------------------------------------------------
# Lifecycle namespace  (argus.lifecycle.*)
# ---------------------------------------------------------------------------

class LifecycleNamespace:
    """``argus.lifecycle`` — script lifecycle events."""

    def __init__(self) -> None:
        self.on_load: CallbackSlot = CallbackSlot()
        self.on_unload: CallbackSlot = CallbackSlot()


# ---------------------------------------------------------------------------
# Events namespace  (argus.events.<subsystem>.<event>)
# ---------------------------------------------------------------------------

# Known subsystem → event names  (mirrors backend/core/injectors/events.py)
_EVENT_REGISTRY: dict[str, list[str]] = {
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


class SubsystemEvents:
    """Event slots for a single subsystem (e.g. ``events.cpu.*``)."""

    def __init__(self, *event_names: str) -> None:
        for name in event_names:
            setattr(self, name, CallbackSlot())


class EventsNamespace:
    """``argus.events`` — subsystem event callbacks."""

    def __init__(self) -> None:
        for sub_name, events in _EVENT_REGISTRY.items():
            setattr(self, sub_name, SubsystemEvents(*events))


# ---------------------------------------------------------------------------
# API namespace  (argus.api.*)
# ---------------------------------------------------------------------------

class ApiNamespace:
    """``argus.api`` — sandbox-safe utility functions."""

    def __init__(self, wrapper: Any) -> None:
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


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def create_argus_namespace(wrapper: Any) -> ModuleType:
    """Create a fresh ``argus`` module namespace for a single script.

    Every call returns an independent instance so scripts are isolated.
    """
    mod = ModuleType("argus")
    mod.lifecycle = LifecycleNamespace()  # type: ignore[attr-defined]
    mod.events = EventsNamespace()  # type: ignore[attr-defined]
    mod.api = ApiNamespace(wrapper)  # type: ignore[attr-defined]
    mod.script = ScriptNamespace()  # type: ignore[attr-defined]
    return mod


# ---------------------------------------------------------------------------
# Callback extraction (after script exec)
# ---------------------------------------------------------------------------

def extract_registered_callbacks(
    argus_mod: ModuleType,
) -> tuple[dict[str, Callable], dict[str, Callable]]:
    """Walk the namespace and collect registered lifecycle & event callbacks.

    Returns ``(lifecycle_callbacks, event_callbacks)`` where keys are dotted
    paths like ``"lifecycle.on_load"`` and ``"events.cpu.on_tick"``.

    Handles both decorator-registered (``CallbackSlot``) and direct-assignment
    (plain callable) slots.
    """
    lifecycle: dict[str, Callable] = {}
    events: dict[str, Callable] = {}

    # -- Lifecycle --
    for name in ("on_load", "on_unload", "on_reload"):
        slot = getattr(argus_mod.lifecycle, name, None)
        cb = _resolve_callback(slot)
        if cb is not None:
            lifecycle[f"lifecycle.{name}"] = cb

    # -- Events --
    for sub_name, event_names in _EVENT_REGISTRY.items():
        subsystem = getattr(argus_mod.events, sub_name, None)
        if subsystem is None:
            continue
        for evt_name in event_names:
            slot = getattr(subsystem, evt_name, None)
            cb = _resolve_callback(slot)
            if cb is not None:
                events[f"events.{sub_name}.{evt_name}"] = cb

    return lifecycle, events


def _resolve_callback(slot: Any) -> Callable | None:
    """Unify decorator and assignment paths into a single callback."""
    if isinstance(slot, CallbackSlot):
        return slot.callback
    if callable(slot):
        return slot
    return None
