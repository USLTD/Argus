"""
Unified ``ctx.data`` callback context types for the Argus hook system.

Every hook — lifecycle, tick, and signal — receives a single ``ctx`` parameter
whose concrete type is one of the three dataclasses below.  Hooks access their
per-hook payload through ``ctx.data`` (typed via ``Generic[T]`` or an explicit
field type).  Shared services such as config, database, driver, and engine are
optionally available on the same object.

Pattern
-------
.. code-block:: python

    def on_before_start(ctx: ScriptContext[SystemMetrics]) -> None:
        print(f"CPU at {ctx.data.cpu.usage_percent}%")
        if ctx.config:
            db.write_snapshot(ctx.data)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Generic, TypedDict, TypeVar

if TYPE_CHECKING:
    from backend.interfaces.caps import SystemMetrics
    from backend.core.driver_proxy import DriverProxy
    from backend.interfaces.plugins import BaseDriver
    from backend.storage.config import ArgusConfig
    from frontend.core.database import DatabaseManager
    from backend.core.engine import BackendEngine


T = TypeVar("T")


@dataclass
class ScriptContext(Generic[T]):
    """Generic context for Python / Lua script lifecycle hooks.

    The ``data`` field carries the per-hook payload (e.g. ``SystemMetrics``
    for ``on_tick``, a ``dict`` for ``on_config_change``).  Shared resources
    are injected lazily and may be ``None`` when the hook runs outside the
    engine lifecycle.
    """

    data: T
    config: ArgusConfig | None = None
    db: DatabaseManager | None = None  # deprecated — will always be None after engine DB decoupling (Phase 3)
    driver: DriverProxy | BaseDriver | None = None


@dataclass
class DriverContext:
    """Context delivered to :meth:`BaseDriver.on_tick` and lifecycle hooks.

    ``data`` holds the latest :class:`SystemMetrics` snapshot when available;
    it is ``None`` during early initialisation ticks.
    """

    data: SystemMetrics | None = None
    engine: BackendEngine | None = None


@dataclass
class BridgeContext:
    """Context delivered to frontend ``EngineBridge`` signal handlers.

    ``data`` contains the aggregate state dict that the bridge publishes to
    the TUI / GUI layer.
    """

    data: "dict" = field(default_factory=dict)
    bridge: "Any | None" = None


# ── Event data payload TypedDicts ──────────────────────────────────────────


class CpuTickData(TypedDict):
    usage_percent: float
    per_core: list[float]
    physical_cores: int
    logical_cores: int


class MemoryTickData(TypedDict):
    total_bytes: int
    used_bytes: int
    available_bytes: int
    percent: float


class DiskTickData(TypedDict):
    mount_point: str
    total_bytes: int
    used_bytes: int
    free_bytes: int
    percent: float


class NetworkTickData(TypedDict):
    bytes_sent: int
    bytes_recv: int
    packets_sent: int
    packets_recv: int


class ProcessTickData(TypedDict):
    pid: int
    name: str
    cpu_percent: float
    memory_rss: int
    status: str
    username: str | None


class GpuTickData(TypedDict):
    name: str
    usage_percent: float
    memory_total: int
    memory_used: int


class BatteryTickData(TypedDict):
    percent: float
    power_plugged: bool | None
    seconds_left: float | None


class SensorTickData(TypedDict):
    name: str
    value: float
    unit: str
    category: str


class UserTickData(TypedDict):
    name: str
    terminal: str | None
    host: str | None
    started: float


class GeneralTickData(TypedDict):
    """Full system state — only TypedDict with `extra` catch-all."""
    cpu: CpuTickData
    ram: MemoryTickData
    processes: list[ProcessTickData] | None
    storage: list[DiskTickData]
    gpu: list[GpuTickData] | None
    network: list[NetworkTickData] | None
    sensors: list[SensorTickData] | None
    battery: BatteryTickData | None
    users: list[UserTickData] | None
    extra: dict[str, object]
