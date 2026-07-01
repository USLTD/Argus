"""Test: generic Protocol for hook callbacks"""

from __future__ import annotations

from typing import Callable, TypeVar, Generic, Protocol, runtime_checkable

from backend.interfaces.contexts import ScriptContext, CpuTickData

T = TypeVar("T", bound=ScriptContext)


class HookCallback(Protocol[T]):
    def __call__(self, ctx: T) -> None: ...


class CpuEvents:
    on_tick: HookCallback[ScriptContext[CpuTickData]] | None

    def __init__(self) -> None:
        self.on_tick = None


cpu = CpuEvents()

# Test 1: Assignment with lambda (does this infer?)
cpu.on_tick = lambda ctx: reveal_type(ctx)  # type: ignore[assignment]


# Test 2: Direct assignment (does this infer?)
def handler_raw(ctx):
    reveal_type(ctx)


cpu.on_tick = handler_raw  # type: ignore[assignment]
