from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, NotRequired, Optional, TypedDict

from .caps import SystemCapabilities, SystemMetrics
from .enums import ConfidenceScore, Permission


class PluginMeta(TypedDict, total=True):
    name: str
    author: str
    version: str
    permissions: list[Permission]
    compatible: NotRequired[list[str] | Callable[[Any], ConfidenceScore | None]]


@dataclass
class PluginContext:
    config: Any = None
    db: Any = None
    driver: Optional[Any] = None


class BasePlugin(ABC):
    """Root interface for all extensions."""


class BaseDriver(BasePlugin, ABC):
    @abstractmethod
    def get_capabilities(self) -> SystemCapabilities:
        pass

    @abstractmethod
    def fetch_metrics(self) -> SystemMetrics:
        pass

    @abstractmethod
    def manage_process(self, pid: int, action: str, **kwargs: Any) -> bool:
        pass


class BaseUserScript(BasePlugin, ABC):
    @abstractmethod
    def execute_tick(self, system_state: dict[str, Any]) -> None:
        pass
