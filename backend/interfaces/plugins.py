from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, NotRequired, TypedDict

if TYPE_CHECKING:
    from backend.interfaces.contexts import DriverContext, ScriptContext
    from backend.storage.config import ArgusConfig
    from frontend.core.database import DatabaseManager

from .caps import (
    BatteryMetric,
    CPUMetric,
    GPUMetric,
    MemoryMetric,
    MetricMetadata,
    MetricsCollection,
    NetworkMetric,
    ProcessMetric,
    SensorMetric,
    StaticSystemInfo,
    StorageMetric,
    SystemCapabilities,
    UserMetric,
)
from .enums import ConfidenceScore, Permission, ScriptExecutionMode
from .sentinels import TickSnapshot, Unavailable


class PluginMeta(TypedDict, total=True):
    name: str
    author: str
    version: str
    permissions: NotRequired[list[Permission]]
    compatible: NotRequired[
        list[str] | Callable[[SystemCapabilities], ConfidenceScore | None]
    ]


@dataclass
class PluginContext:
    argus_config: ArgusConfig | None = None
    db: DatabaseManager | None = None
    driver: BaseDriver | None = None


class BasePlugin(ABC):
    """Root interface for all extensions."""


class BaseDriver(BasePlugin, ABC):
    def __init__(self) -> None:
        self._initialized: bool = False
        self._cached_static_info: StaticSystemInfo | None = None
        # internal setup
        self.on_load()
        self._initialized = True

    def on_load(self, ctx: DriverContext | None = None) -> None:
        """Called after driver instantiation.

        Override only if you understand the driver lifecycle.
        Default: no-op.
        """

    def on_unload(self, ctx: DriverContext | None = None) -> None:
        """Called during driver disposal.

        Override only if you understand the driver lifecycle.
        Default: no-op.
        """

    def dispose(self) -> None:
        """INTERNAL: calls on_unload(). Driver devs should not override."""
        self.on_unload()

    def __enter__(self) -> BaseDriver:
        return self

    def __exit__(self, *args: object) -> None:
        self.dispose()

    # ── Per-subsystem tick methods ──────────────────────────────

    def tick_cpu(
        self, ctx: DriverContext
    ) -> MetricsCollection[CPUMetric] | Unavailable:
        """CPU usage, core counts. Override to implement."""
        return Unavailable("unsupported", "CPU monitoring not implemented")

    def tick_memory(
        self, ctx: DriverContext
    ) -> MetricsCollection[MemoryMetric] | Unavailable:
        """RAM total, used, available, percent. Override to implement."""
        return Unavailable("unsupported", "Memory monitoring not implemented")

    def tick_disk(
        self, ctx: DriverContext
    ) -> MetricsCollection[StorageMetric] | Unavailable:
        """Per-mount-point disk usage. Override to implement."""
        return Unavailable("unsupported", "Disk monitoring not implemented")

    def tick_network(
        self, ctx: DriverContext
    ) -> MetricsCollection[NetworkMetric] | Unavailable:
        """Per-interface network I/O counters. Override to implement."""
        return Unavailable("unsupported", "Network monitoring not implemented")

    def tick_processes(
        self, ctx: DriverContext
    ) -> MetricsCollection[ProcessMetric] | Unavailable:
        """Snapshot of running processes. Override to implement."""
        return Unavailable("unsupported", "Process listing not implemented")

    def tick_gpu(
        self, ctx: DriverContext
    ) -> MetricsCollection[GPUMetric] | Unavailable:
        """Per-GPU metrics. Override to implement."""
        return Unavailable("unsupported", "GPU monitoring not implemented")

    def tick_sensors(
        self, ctx: DriverContext
    ) -> MetricsCollection[SensorMetric] | Unavailable:
        """Temperature/voltage/fan sensors. Override to implement."""
        return Unavailable("unsupported", "Sensor monitoring not implemented")

    def tick_battery(
        self, ctx: DriverContext
    ) -> MetricsCollection[BatteryMetric] | Unavailable:
        """Battery charge, status. Override to implement."""
        return Unavailable("unsupported", "Battery monitoring not implemented")

    def tick_users(
        self, ctx: DriverContext
    ) -> MetricsCollection[UserMetric] | Unavailable:
        """Logged-in users. Override to implement."""
        return Unavailable("unsupported", "User monitoring not implemented")

    # ── Aggregate tick ─────────────────────────────────────────────

    def tick(self, ctx: DriverContext) -> TickSnapshot:
        """Call all per-subsystem methods. Override for batching."""
        return TickSnapshot(
            cpu=self.tick_cpu(ctx),
            memory=self.tick_memory(ctx),
            processes=self.tick_processes(ctx),
            disk=self.tick_disk(ctx),
            network=self.tick_network(ctx),
            gpu=self.tick_gpu(ctx),
            sensors=self.tick_sensors(ctx),
            battery=self.tick_battery(ctx),
            users=self.tick_users(ctx),
        )

    def _collect_static_info(self) -> StaticSystemInfo | None:
        """Collect static system information from scratch.

        Override in concrete drivers to provide motherboard, BIOS, GPU model, etc.
        Default: returns None.
        """
        return None

    def get_static_info(self) -> StaticSystemInfo | None:
        """Return static system information, or None if unavailable.

        Results are cached after the first call since system info never
        changes during a session. Call invalidate_static_cache() to force
        a fresh collection if needed.
        """
        if self._cached_static_info is not None:
            return self._cached_static_info
        info = self._collect_static_info()
        self._cached_static_info = info
        return info

    def invalidate_static_cache(self) -> None:
        """Drop the cached static info so the next call re-collects."""
        self._cached_static_info = None

    @abstractmethod
    def get_capabilities(self) -> SystemCapabilities:
        pass

    @abstractmethod
    def manage_process(self, pid: int, action: str, **kwargs: Any) -> bool:
        pass


class BaseUserScript(BasePlugin):
    """Base class for user scripts (Lua, Python). Default methods are no-ops."""

    file_path: Path | None = None
    METADATA: PluginMeta | None = None
    execution_mode: ScriptExecutionMode = ScriptExecutionMode.NONBLOCKING

    def bind_driver(self, driver: BaseDriver | None) -> None:
        """Optional: receive the active driver reference."""

    def trigger_load(self, ctx: ScriptContext[None]) -> None:
        """Optional: called when the script is activated."""

    def trigger_unload(self, ctx: ScriptContext[None]) -> None:
        """Optional: called when the script is about to be unloaded."""

    def dispatch(self, event_path: str, data: Any = None) -> None:
        """Dispatch a named event to callbacks."""

    def pop_output(self) -> list[str]:
        """Return and clear captured output."""
        return []
