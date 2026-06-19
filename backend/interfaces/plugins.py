from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Callable
from typing import Any, NotRequired, TypedDict

from .caps import StaticSystemInfo, SystemCapabilities, SystemMetrics
from .enums import ConfidenceScore, Permission


class PluginMeta(TypedDict, total=True):
    name: str
    author: str
    version: str
    permissions: NotRequired[list[Permission]]
    compatible: NotRequired[list[str] | Callable[[Any], ConfidenceScore | None]]


@dataclass
class PluginContext:
    config: Any = None
    db: Any = None
    driver: Any | None = None


class BasePlugin(ABC):
    """Root interface for all extensions."""


class BaseDriver(BasePlugin, ABC):
    def __init__(self) -> None:
        self._initialized: bool = False
        # internal setup
        self.on_load()
        self._initialized = True

    def on_load(self) -> None:
        """Called after driver instantiation.

        Override only if you understand the driver lifecycle.
        Default: no-op.
        """

    def on_unload(self) -> None:
        """Called during driver disposal.

        Override only if you understand the driver lifecycle.
        Default: no-op.
        """

    def dispose(self) -> None:
        """INTERNAL: calls on_unload(). Driver devs should not override."""
        self.on_unload()

    def __enter__(self) -> BaseDriver:
        return self

    def __exit__(self, *args: Any) -> None:
        self.dispose()

    @abstractmethod
    def on_tick(self) -> SystemMetrics:
        """Called each engine tick. Return current system metrics.

        This replaces the old ``fetch_metrics``. The driver produces
        data ONLY when the engine calls this method.
        """

    def get_static_info(self) -> StaticSystemInfo | None:
        """Return static system information, or None if unavailable.

        Override to provide motherboard, BIOS, GPU model, etc.
        Default: returns None.
        """
        return None

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

    def bind_driver(self, driver: Any) -> None:
        """Optional: receive the active driver reference."""

    def trigger_load(self, ctx: Any) -> None:
        """Optional: called when the script is activated."""

    def trigger_unload(self, ctx: Any) -> None:
        """Optional: called when the script is about to be unloaded."""

    def dispatch(self, event_path: str, data: Any = None) -> None:
        """Dispatch a named event to callbacks."""

    def pop_output(self) -> list[str]:
        """Return and clear captured output."""
        return []
