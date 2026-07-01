from typing import final, TypeVar, ParamSpec, Callable, Any
from backend.core.driver_proxy import DriverProxy as _DriverProxy
from backend.interfaces.caps import SystemMetrics
from backend.storage.config import ArgusConfig as _ArgusConfig
from frontend.core.database import DatabaseManager as _DatabaseManager

P = ParamSpec("P")
R = TypeVar("R")


# ---------------------------------------------------------------------------
# Context types
# ---------------------------------------------------------------------------
@final
class ScriptContext[T]:
    """Runtime context passed to lifecycle hooks and event callbacks.

    Scripts access per-hook data via ``ctx.data``.
    """

    data: T
    config: _ArgusConfig | None = None
    db: _DatabaseManager | None = None
    driver: _DriverProxy | None = None


@final
class DriverContext:
    """Context passed to driver lifecycle hooks."""

    data: SystemMetrics | None = None
    engine: object = None


# ---------------------------------------------------------------------------
# Callback slot (``Hook`` is the decorator/assignment type)
# ---------------------------------------------------------------------------
@final
class Hook:
    """
    Supports both ``@decorator`` and ``direct-assignment`` syntax.

    * ``@argus.lifecycle.on_load`` — registers *func* via decorator.
    * ``argus.events.cpu.on_tick = my_func`` — registers by assignment.
    """

    callback: Callable[..., Any] | None

    def __call__(self, func: Callable[P, R]) -> Callable[P, R]:
        ...