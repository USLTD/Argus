"""Permission-gated driver proxy for script contexts.

Drivers do not have permissions — any attempt to gate access behind
driver-specific permissions raises PermissionError.
"""

from __future__ import annotations

from typing import Any, final

from backend.interfaces.caps import SystemCapabilities
from backend.interfaces.enums import Permission
from backend.interfaces.plugins import BaseDriver, PluginMeta


@final
class DriverProxy:
    """
    Wraps a driver and exposes its capabilities / metadata.

    *perms* is accepted for backward compatibility with script contexts,
    but driver permissions are no longer enforced — all driver data is
    accessible to any script that has a driver reference.
    """

    __slots__ = ("_driver", "_perms", "_meta")

    def __init__(
        self,
        driver: BaseDriver | None,
        perms: set[Permission] | None = None,
        meta: PluginMeta | None = None,
    ) -> None:
        self._driver = driver
        self._perms = perms or set()
        self._meta = meta

    @property
    def capabilities(self) -> SystemCapabilities | None:
        if self._driver is None:
            return None
        return self._driver.get_capabilities()

    @property
    def metadata(self) -> PluginMeta | None:
        return self._meta

    # --- passthrough for driver methods that scripts may call ---
    def __getattr__(self, name: str) -> Any:
        if self._driver is None:
            raise AttributeError(f"Driver not available: {name}")
        return getattr(self._driver, name)
