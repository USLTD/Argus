"""Python type stub for driver and script authors.

Usage
-----
Copy this file to your project and import the types::

    from plugins import DriverBase, PluginMeta, Permission, PluginContext

Metadata
--------
Every Python driver and script module **must** define::

    METADATA: PluginMeta = {
        "name": "my-plugin",
        "author": "You",
        "version": "1.0.0",
        "permissions": [Permission.SCRIPT_READ],
    }

Drivers additionally **must** define::

    DRIVER = MyDriver  # reference to the driver class, not an instance

Compatibility (optional)
-----------------------
Declarative rules (:class:`list[str]`)::

    compatible = [
        "sys.platform EQ 'win32' -> FULL",
        "platform.system EQ 'Linux' -> HIGH",
    ]

Callable (drivers only)::

    def check_compat(ctx: CompatContext) -> ConfidenceScore | None:
        if ctx.sys.platform.startswith("win32"):
            return ConfidenceScore.FULL
        return None

    METADATA = { ..., "compatible": check_compat }
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, NotRequired, TypedDict

if TYPE_CHECKING:
    from backend.interfaces.contexts import DriverContext, ScriptContext
    from backend.storage.config import ArgusConfig as _ArgusConfig
    from backend.storage.database import DatabaseManager as _DatabaseManager

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
    SystemMetrics,
)
from backend.interfaces.sentinels import TickSnapshot, Unavailable
from .enums import ConfidenceScore, Permission


class PluginMeta(TypedDict, total=True):
    """Required metadata for every plugin module.

    Declared as a module-level ``METADATA`` constant, **not** as a class
    attribute.

    Example::

        METADATA: PluginMeta = {
            "name": "cpu-monitor",
            "author": "Argus Team",
            "version": "2.1.0",
        }
    """

    name: str
    """Human-readable plugin name."""

    author: str
    """Author or organisation name."""

    version: str
    """Semantic version string (e.g. ``"1.0.0"``)."""

    permissions: NotRequired[list[Permission]]
    """List of :class:`Permission` values the plugin requires."""

    compatible: NotRequired[list[str] | Callable[[SystemCapabilities], ConfidenceScore | None]]
    """Optional compatibility rules.

    * Declarative: ``["sys.platform EQ 'win32' -> FULL"]``
    * Callable (drivers only): ``Callable[[SystemCapabilities], ConfidenceScore | None]``
    """


@dataclass
class PluginContext:
    """Runtime context passed to lifecycle hooks."""

    argus_config: _ArgusConfig | None = None
    """Application config object."""

    db: _DatabaseManager | None = None
    """Database manager instance (or ``None``)."""

    driver: BaseDriver | None = None
    """Active hardware driver instance (or ``None``)."""


class BasePlugin(ABC):
    """Root interface for all extensions."""


class BaseDriver(BasePlugin, ABC):
    """Extend this class to implement a hardware driver.

    Must be referenced from the module-level ``DRIVER`` constant::

        DRIVER = MyDriver  # not an instance
    """

    _initialized: bool

    def __init__(self) -> None: ...

    def on_load(self, ctx: DriverContext | None = None) -> None:
        """Called after driver instantiation. Default: no-op."""

    def on_unload(self, ctx: DriverContext | None = None) -> None:
        """Called during driver disposal. Default: no-op."""

    def dispose(self) -> None:
        """INTERNAL: calls on_unload(). Driver devs should not override."""

    def __enter__(self) -> BaseDriver: ...

    def __exit__(self, *args: object) -> None: ...

    def tick(self, ctx: DriverContext) -> TickSnapshot:
        """Called each engine tick. Aggregate subsystem data into TickSnapshot."""

    @abstractmethod
    def tick_cpu(self, ctx: DriverContext) -> MetricsCollection[CPUMetric] | Unavailable:
        """CPU usage, core counts."""

    @abstractmethod
    def tick_memory(self, ctx: DriverContext) -> MetricsCollection[MemoryMetric] | Unavailable:
        """RAM total, used, available, percent."""

    @abstractmethod
    def tick_processes(self, ctx: DriverContext) -> MetricsCollection[ProcessMetric] | Unavailable:
        """Snapshot of running processes."""

    @abstractmethod
    def tick_disk(self, ctx: DriverContext) -> MetricsCollection[StorageMetric] | Unavailable:
        """Per-mount-point disk usage."""

    @abstractmethod
    def tick_network(self, ctx: DriverContext) -> MetricsCollection[NetworkMetric] | Unavailable:
        """Per-interface network I/O counters."""

    @abstractmethod
    def tick_gpu(self, ctx: DriverContext) -> MetricsCollection[GPUMetric] | Unavailable:
        """Per-GPU metrics."""

    @abstractmethod
    def tick_sensors(self, ctx: DriverContext) -> MetricsCollection[SensorMetric] | Unavailable:
        """Temperature/voltage/fan sensors."""

    @abstractmethod
    def tick_battery(self, ctx: DriverContext) -> MetricsCollection[BatteryMetric] | Unavailable:
        """Battery charge, status."""

    def get_static_info(self) -> StaticSystemInfo | None:
        """Return static system information, or None if unavailable.

        Default: returns None.
        """

    @abstractmethod
    def get_capabilities(self) -> SystemCapabilities:
        """Return the static capabilities of this driver."""

    @abstractmethod
    def manage_process(self, pid: int, action: str, **kwargs: Any) -> bool:
        """Manage a process by PID.

        Actions: ``"kill"``.
        """


class BaseUserScript:
    """Base class for user scripts (Lua, Python). Default methods are no-ops.

    Python user scripts no longer subclass this class directly.
    Instead use ``import argus`` with decorator-based callbacks.
    """

    file_path: Path | None
    """Path to the script file."""

    METADATA: PluginMeta | None
    """Cached metadata dict extracted from the script."""

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
