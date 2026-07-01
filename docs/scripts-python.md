# Python Scripting

## Overview

Python scripts are user-authored `.py` files dropped into the `scripts/`
directory. The engine discovers them at startup through the same
`DiscoveryLoader` that finds drivers, evaluates compatibility metadata, and
loads compatible scripts into an isolated `argus` namespace.

Each script gets its own namespace via `argus_runtime.create_argus_namespace()`,
so callbacks registered by one script never leak into another. Scripts use a
plain `import argus` and register callbacks through decorators or direct
assignment on `argus.events.<subsystem>` and `argus.lifecycle` slots.

## Hook API

Python scripts can register callbacks on lifecycle events and per-subsystem
tick events. All callbacks receive a single `ctx` parameter of type
`ScriptContext[T]`, where `T` matches the event payload.

### Lifecycle hooks

```python
import argus

@argus.lifecycle.on_load
def on_load(ctx: ScriptContext[None]) -> None:
    ...  # called once when the script is loaded

@argus.lifecycle.on_unload
def on_unload(ctx: ScriptContext[None]) -> None:
    ...  # called once when the script is unloaded
```

### Subsystem event hooks

Each monitored subsystem exposes an `on_tick` slot. The `ctx.data` payload
type varies by subsystem.

```python
@argus.events.cpu.on_tick
def on_cpu(ctx: ScriptContext[CpuTickData]) -> None:
    print(f"CPU: {ctx.data['usage_percent']}%")

@argus.events.memory.on_tick
def on_memory(ctx: ScriptContext[MemoryTickData]) -> None:
    print(f"RAM: {ctx.data['percent']}%")

@argus.events.disk.on_tick
def on_disk(ctx: ScriptContext[list[DiskTickData]]) -> None:
    for vol in ctx.data:
        print(f"{vol['mount_point']}: {vol['percent']}%")

@argus.events.net.on_tick
def on_net(ctx: ScriptContext[list[NetworkTickData]]) -> None:
    ...  # per-interface network stats

@argus.events.process.on_tick
def on_proc(ctx: ScriptContext[list[ProcessTickData]]) -> None:
    ...  # running processes snapshot

@argus.events.gpu.on_tick
def on_gpu(ctx: ScriptContext[GpuTickData | None]) -> None:
    ...  # GPU usage (None if no GPU)

@argus.events.battery.on_tick
def on_bat(ctx: ScriptContext[BatteryTickData | None]) -> None:
    ...  # battery status

@argus.events.sensor.on_tick
def on_sensor(ctx: ScriptContext[list[SensorTickData] | None]) -> None:
    ...  # temperature/fan sensors

@argus.events.users.on_tick
def on_users(ctx: ScriptContext[list[UserTickData] | None]) -> None:
    ...  # logged-in users

@argus.events.general.on_tick
def on_tick(ctx: ScriptContext[GeneralTickData]) -> None:
    ...  # full system state in one callback
```

General tick data (the `GeneralTickData` TypedDict) aggregates the entire
system state: CPU, RAM, processes, storage, GPU, network, sensors, battery,
and users.

### Engine lifecycle hooks (planned)

The following general-purpose hooks are documented in the scripting reference
but are not yet wired to the engine dispatch loop:

- `on_tick(ctx: ScriptContext[SystemMetrics])` -- called every tick
- `on_start(ctx: ScriptContext[None])` -- on engine start
- `on_stop(ctx: ScriptContext[None])` -- on engine stop
- `on_config_change(ctx: ScriptContext[dict])` -- on config reload

Use the per-subsystem event hooks (above) for tick data in the current
release.

## ScriptContext

Every callback receives a `ScriptContext[T]` dataclass instance.

| Field    | Type                           | Description                         |
|----------|--------------------------------|-------------------------------------|
| `data`   | `T` (generic payload)          | Per-hook payload (TypedDict, etc.) |
| `config` | `ArgusConfig \| None`          | Application configuration           |
| `driver` | `DriverProxy \| BaseDriver \| None` | Active driver proxy            |
| `db`     | `DatabaseManager \| None`      | Database handle (deprecated)        |

The `data` field carries the event-specific payload. For `on_tick` hooks this
is the subsystem TypedDict (e.g. `CpuTickData`, `MemoryTickData`). For
lifecycle hooks it is `None`.

`config`, `driver`, and `db` are injected lazily by the engine and may be
`None` when the hook runs outside the engine lifecycle.

## Execution modes

Each script declares an execution mode via its `METADATA` or a default
assigned by the engine.

| Mode           | Enum value                          | Behavior |
|----------------|-------------------------------------|----------|
| **BLOCKING**   | `ScriptExecutionMode.BLOCKING`      | Script runs synchronously in the tick loop. Blocks the next tick until done. |
| **NONBLOCKING**| `ScriptExecutionMode.NONBLOCKING`   | Script runs in a thread pool executor. Does not block the tick loop. |
| **MIXED**      | `ScriptExecutionMode.MIXED`         | Lifecycle hooks run synchronously; tick hooks run in the thread pool. |

NONBLOCKING is the default. Use BLOCKING only for scripts that must complete
before the next tick (rare).

## Script metadata

Scripts declare metadata in a module-level `METADATA` dict:

```python
import argus
from argus.script import Permission

METADATA: argus.script.Metadata = {
    "name": "My Script",
    "author": "You",
    "version": "1.0.0",
    "permissions": [Permission.SYSTEM_READ],
    "compatible": [
        "sys.platform EQ 'win32' -> TRUE",
        "sys.platform EQ 'linux' -> TRUE",
    ],
}
```

The `compatible` list uses the same compatibility rule syntax as drivers. A
script whose rules all evaluate to true is loaded; otherwise it is skipped.

## Example 1: CPU Logger

Source: `scripts/cpu_logger.py`

```python
"""CPU Logger — prints CPU usage and core count on each tick."""

from __future__ import annotations

import argus

METADATA: argus.script.Metadata = {
    "name": "CPU Logger",
    "author": "Argus Team",
    "version": "2.0.0",
    "compatible": [
        "sys.platform EQ 'win32' -> TRUE",
        "sys.platform EQ 'linux' -> TRUE",
        "sys.platform EQ 'darwin' -> TRUE",
    ],
}


@argus.lifecycle.on_load
def on_load(ctx) -> None:
    argus.api.print("Loading CPU Logger...")


@argus.lifecycle.on_unload
def on_unload(ctx) -> None:
    argus.api.print("Unloading CPU Logger...")


@argus.events.cpu.on_tick
def on_cpu(ctx: object) -> None:
    data = ctx.data
    cores = data.get("physical_cores", "?")
    threads = data.get("logical_cores", "?")
    print(f"[CPU] {data['usage_percent']:.1f}% ({cores}C/{threads}T)")
```

This script:
- Declares compatibility with Windows, Linux, and macOS.
- Prints a startup and shutdown message via lifecycle hooks.
- On each CPU tick, prints aggregate usage percent plus core/thread count.

## Example 2: Multi-Subsystem Monitor

Source: `scripts/multi_subsystem.py`

```python
"""Multi-Subsystem Reporter — prints CPU, RAM, top process, and GPU."""

from __future__ import annotations

from typing import TYPE_CHECKING

import argus

if TYPE_CHECKING:
    from backend.interfaces.contexts import (
        CpuTickData, GeneralTickData, MemoryTickData, ScriptContext,
    )

METADATA: argus.script.Metadata = {
    "name": "Multi-Subsystem Reporter",
    "author": "Argus Team",
    "version": "2.0.0",
    "permissions": [argus.script.Permission.SYSTEM_READ],
    "compatible": [
        "sys.platform EQ 'win32' -> TRUE",
        "sys.platform EQ 'linux' -> TRUE",
        "sys.platform EQ 'darwin' -> TRUE",
    ],
}


cpu_data: dict[str, float] = {}
ram_data: dict[str, float] = {}


@argus.events.cpu.on_tick
def on_cpu(ctx: ScriptContext[CpuTickData]) -> None:
    cpu_data["percent"] = ctx.data["usage_percent"]


@argus.events.memory.on_tick
def on_memory(ctx: ScriptContext[MemoryTickData]) -> None:
    ram_data["percent"] = ctx.data["percent"]


@argus.events.general.on_tick
def on_tick(ctx: ScriptContext[GeneralTickData]) -> None:
    state = ctx.data
    parts = []
    parts.append(f"CPU {state['cpu']['usage_percent']:.1f}%")
    parts.append(f"RAM {state['ram']['percent']:.1f}%")

    procs = state.get("processes")
    if procs:
        top = max(procs, key=lambda p: p["cpu_percent"])
        parts.append(f"Top: {top['name']} @ {top['cpu_percent']:.1f}%")

    gpu = state.get("gpu")
    if gpu:
        g = gpu[0]
        parts.append(f"{g['name']} @ {g['usage_percent']:.0f}%")

    print(" | ".join(parts))
```

This script:
- Subscribes to subsystem-specific tick hooks (`cpu`, `memory`) to cache data.
- Uses `events.general.on_tick` to receive the full system state in one
  callback and combine CPU, RAM, top process, and GPU into a single report
  line.
- Demonstrates both per-subsystem and general tick subscriptions together.

## Best practices

**Error handling.** Wrap callback bodies in try/except. An unhandled exception
silently disables the callback for the current tick but does not crash the
engine.

```python
@argus.events.cpu.on_tick
def on_cpu(ctx):
    try:
        ...
    except Exception as exc:
        print(f"CPU callback error: {exc}")
```

**Performance.** Keep callbacks fast. Tick data arrives every 2 seconds by
default. If you need to do heavy work (HTTP calls, file writes), use
`argus.api.sleep(ms)` to skip ticks.

**Avoid infinite loops.** Do not call `argus.events.*` registration inside a
callback. Do not use `while True` loops. The engine never preempts a running
callback.

**Print vs. log.** Use `argus.api.print()` or the built-in `print()` (which is
aliased to the same function). Output is captured per-script and can be
retrieved via the engine's `pop_output()` API. Do not write to `sys.stdout`
directly.

**Module-level state.** Module globals persist across ticks. Use them to cache
data, track deltas, or implement debounce logic (as `multi_subsystem.py`
does).
