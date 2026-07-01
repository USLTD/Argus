"""Type aliases for script callback context types.

Usage::

    from argus.types import CpuCtx, MemCtx

    @argus.events.cpu.on_tick
    def handler(ctx: CpuCtx) -> None:
        print(ctx.data.usage_percent)
"""

from backend.interfaces.contexts import (
    ScriptContext,
    CpuTickData,
    MemoryTickData,
    DiskTickData,
    NetworkTickData,
    ProcessTickData,
    GpuTickData,
    BatteryTickData,
    SensorTickData,
    UserTickData,
    GeneralTickData,
)

# ── Per-subsystem context aliases ──────────────────────────

CpuCtx: type = ScriptContext[CpuTickData]
"""Callback context for ``events.cpu.on_tick``.
``ctx.data`` exposes :class:`CpuTickData`: ``usage_percent``, ``per_core``,
``physical_cores``, ``logical_cores``.
"""

MemCtx: type = ScriptContext[MemoryTickData]
"""Callback context for ``events.memory.on_tick``.
``ctx.data`` exposes :class:`MemoryTickData`: ``total_bytes``, ``used_bytes``,
``available_bytes``, ``percent``.
"""

DiskCtx: type = ScriptContext[list[DiskTickData]]
"""Callback context for ``events.disk.on_tick``.
``ctx.data`` is a list of :class:`DiskTickData`, one per mount point.
"""

NetCtx: type = ScriptContext[list[NetworkTickData]]
"""Callback context for ``events.net.on_tick``.
``ctx.data`` is a list of :class:`NetworkTickData`, one per interface.
"""

ProcCtx: type = ScriptContext[list[ProcessTickData]]
"""Callback context for ``events.process.on_tick``.
``ctx.data`` is a list of :class:`ProcessTickData`.
"""

GpuCtx: type = ScriptContext[GpuTickData | None]
"""Callback context for ``events.gpu.on_tick``.
``None`` when no GPU is available.
"""

BatCtx: type = ScriptContext[BatteryTickData | None]
"""Callback context for ``events.battery.on_tick``.
``None`` when no battery is present.
"""

SensorCtx: type = ScriptContext[list[SensorTickData] | None]
"""Callback context for ``events.sensor.on_tick``.
``None`` when no sensors are available.
"""

UserCtx: type = ScriptContext[list[UserTickData] | None]
"""Callback context for ``events.users.on_tick``.
``None`` when no users are logged in.
"""

# ── Broad context aliases ──────────────────────────────────

GeneralCtx: type = ScriptContext[GeneralTickData]
"""Callback context for ``events.general.on_tick``.
Full system state in ``ctx.data``.
"""

LifecycleCtx: type = ScriptContext[None]
"""Callback context for ``lifecycle.on_load`` / ``on_unload``.
``ctx.data`` is ``None``.
"""
