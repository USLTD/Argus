"""Permission-gated driver proxy for script contexts."""

from __future__ import annotations

from typing import Any, final

from backend.interfaces.caps import SystemCapabilities
from backend.interfaces.enums import Permission
from backend.interfaces.plugins import BaseDriver, PluginMeta

@final
class DriverProxy:
    """
    Wraps a driver and gates .capabilities / .metadata behind DRIVER_READ_* permissions.

    Scripts access the driver via ``ctx.driver`` in lifecycle callbacks.
    """

    __slots__ = ("_driver", "_perms", "_meta")

    def __init__(self, driver: BaseDriver | None, perms: set[Permission], meta: PluginMeta | None = None) -> None:
        self._driver = driver
        self._perms = perms
        self._meta = meta

    @property
    def capabilities(self) -> SystemCapabilities | None:
        if self._driver is None:
            return None
        if Permission.DRIVER_READ_CAPABILITIES not in self._perms:
            return None
        return self._driver.get_capabilities()

    @property
    def metadata(self) -> PluginMeta | None:
        if self._driver is None:
            return None
        if Permission.DRIVER_READ_METADATA not in self._perms:
            return None
        return self._meta

    # --- passthrough for driver methods that scripts may call ---
    def __getattr__(self, name: str) -> Any:
        if self._driver is None:
            raise AttributeError(f"Driver not available: {name}")
        return getattr(self._driver, name)
