"""Synchronous driver bridge with NO PyQt6 dependency.

Used by Textual TUI and CLI tools. Every call to a get_*() method
re-fetches from the driver via tick_all() to ensure fresh data.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from backend.bridges.converters import (
    battery_collection_to_dict,
    cpu_collection_to_dict,
    disk_collection_to_dict,
    memory_collection_to_dict,
    network_collection_to_dict,
    process_collection_to_dict,
    sensor_collection_to_dict,
)

if TYPE_CHECKING:
    from backend.interfaces.enums import Permission
    from backend.interfaces.plugins import BaseDriver
    from backend.interfaces.sentinels import TickSnapshot


class SyncBridge:
    """Bridge that wraps a BaseDriver synchronously.

    Provides the same TypedDict-shaped outputs as EngineBridge
    but without PyQt6 or timer-based polling.
    """

    def __init__(self, driver: BaseDriver, permissions: set[Permission] | None = None) -> None:
        self._driver = driver
        self._permissions = permissions
        self._snapshot: TickSnapshot | None = None

    # ── permission check ──────────────────────────────────────────

    def _check(self, required: Permission) -> bool:
        """Check if the bridge's permissions satisfy *required*.

        None = unrestricted (frontend use). Empty set = no data.
        """
        if self._permissions is None:
            return True
        from backend.interfaces.permissions import PermissionHierarchy

        return any(
            PermissionHierarchy.grants(p, required) for p in self._permissions
        )

    # ── lifecycle ──────────────────────────────────────────────────

    def tick_all(self) -> None:
        """Refresh all metrics from the driver."""
        from backend.interfaces.contexts import DriverContext

        ctx = DriverContext()
        self._snapshot = self._driver.tick(ctx)

    # ── per-subsystem getters ──────────────────────────────────────

    def get_cpu_metrics(self) -> dict:
        """Return CPU metrics as a flat dict."""
        from backend.interfaces.enums import Permission
        if not self._check(Permission.CPU_READ):
            return {"cpu_percent": 0.0, "per_core": [], "frequency": None, "physical_cores": 0, "logical_cores": 0}
        from backend.interfaces.sentinels import Unavailable

        snap = self._snapshot
        if snap is None:
            return {"cpu_percent": 0.0, "per_core": [], "frequency": None, "physical_cores": 0, "logical_cores": 0}
        if isinstance(snap.cpu, Unavailable):
            return {"cpu_percent": 0.0, "per_core": [], "frequency": None, "physical_cores": 0, "logical_cores": 0}
        static = self._driver.get_static_info()
        return cpu_collection_to_dict(
            snap.cpu,
            static_cores=getattr(static, "cpu_physical_cores", 0) if static else 0,
            static_threads=getattr(static, "cpu_logical_cores", 0) if static else 0,
        )

    def get_memory_metrics(self) -> dict:
        """Return memory metrics as a flat dict."""
        from backend.interfaces.enums import Permission
        if not self._check(Permission.MEMORY_READ):
            return {"total": 0, "used": 0, "available": 0, "free": 0, "cached": 0, "percent": 0.0}
        from backend.interfaces.sentinels import Unavailable

        snap = self._snapshot
        if snap is None:
            return {"total": 0, "used": 0, "available": 0, "free": 0, "cached": 0, "percent": 0.0}
        if isinstance(snap.memory, Unavailable):
            return {"total": 0, "used": 0, "available": 0, "free": 0, "cached": 0, "percent": 0.0}
        return memory_collection_to_dict(snap.memory)

    def get_disk_usage(self, path: str = "/") -> dict:
        """Return disk usage for *path* as a flat dict."""
        from backend.interfaces.enums import Permission
        if not self._check(Permission.DISK_READ):
            return {"total": 0, "used": 0, "free": 0, "percent": 0.0}
        from backend.interfaces.sentinels import Unavailable

        snap = self._snapshot
        if snap is None:
            return {"total": 0, "used": 0, "free": 0, "percent": 0.0}
        if isinstance(snap.disk, Unavailable):
            return {"total": 0, "used": 0, "free": 0, "percent": 0.0}
        return disk_collection_to_dict(snap.disk, mount_point=path)

    def get_network_io(self) -> dict:
        """Return aggregate network IO as a flat dict."""
        from backend.interfaces.enums import Permission
        if not self._check(Permission.NETWORK_READ):
            return {"bytes_sent": 0, "bytes_recv": 0}
        from backend.interfaces.sentinels import Unavailable

        snap = self._snapshot
        if snap is None:
            return {"bytes_sent": 0, "bytes_recv": 0}
        if isinstance(snap.network, Unavailable):
            return {"bytes_sent": 0, "bytes_recv": 0}
        return network_collection_to_dict(snap.network)

    def get_process_list(self) -> list[dict]:
        """Return process list as a list of flat dicts."""
        from backend.interfaces.enums import Permission
        if not self._check(Permission.PROCESSES_READ):
            return []
        from backend.interfaces.sentinels import Unavailable

        snap = self._snapshot
        if snap is None:
            return []
        if isinstance(snap.processes, Unavailable):
            return []
        return process_collection_to_dict(snap.processes)

    def get_sensors(self) -> dict:
        """Return sensor temperatures as a dict of name -> list of values."""
        from backend.interfaces.enums import Permission
        if not self._check(Permission.SENSORS_READ):
            return {"temperatures": {}}
        from backend.interfaces.sentinels import Unavailable

        snap = self._snapshot
        if snap is None:
            return {"temperatures": {}}
        if isinstance(snap.sensors, Unavailable):
            return {"temperatures": {}}
        return sensor_collection_to_dict(snap.sensors)

    def get_battery(self) -> dict:
        """Return battery info as a flat dict."""
        from backend.interfaces.enums import Permission
        if not self._check(Permission.BATTERY_READ):
            return {"percent": 0.0, "power_plugged": None, "seconds_left": None}
        from backend.interfaces.sentinels import Unavailable

        snap = self._snapshot
        if snap is None:
            return {"percent": 0.0, "power_plugged": None, "seconds_left": None}
        if isinstance(snap.battery, Unavailable):
            return {"percent": 0.0, "power_plugged": None, "seconds_left": None}
        return battery_collection_to_dict(snap.battery)

    def get_static_info(self) -> dict:
        """Return static system info as a dict."""
        from backend.interfaces.enums import Permission
        if not self._check(Permission.SYSTEM_READ):
            return {}
        info = self._driver.get_static_info()
        if info is None:
            return {}
        return {
            "hostname": getattr(info, "hostname", ""),
            "platform": getattr(info, "platform", ""),
            "platform_version": getattr(info, "platform_version", ""),
            "cpu_brand": getattr(info, "cpu_brand", ""),
            "cpu_physical_cores": getattr(info, "cpu_physical_cores", 0),
            "cpu_logical_cores": getattr(info, "cpu_logical_cores", 0),
            "total_ram": getattr(info, "total_ram", 0),
        }

    def get_boot_time(self) -> float:
        """Return boot time timestamp."""
        from backend.interfaces.enums import Permission
        if not self._check(Permission.SYSTEM_READ):
            return 0.0
        info = self._driver.get_static_info()
        if info is None:
            return 0.0
        return getattr(info, "boot_time", 0.0)

    def terminate_process(self, pid: int) -> bool:
        """Ask the driver to terminate *pid* gracefully."""
        from backend.interfaces.enums import Permission
        if not self._check(Permission.PROCESSES_WRITE):
            return False
        try:
            return self._driver.manage_process(pid, "terminate")
        except Exception:
            return False

    def kill_process(self, pid: int) -> bool:
        """Ask the driver to force-kill *pid*."""
        from backend.interfaces.enums import Permission
        if not self._check(Permission.PROCESSES_EXECUTE):
            return False
        try:
            return self._driver.manage_process(pid, "kill")
        except Exception:
            return False

    def get_all(self) -> dict:
        """Return ALL metrics as one dict. Similar to EngineBridge.get_all()."""
        self.tick_all()
        cpu = self.get_cpu_metrics()
        memory = self.get_memory_metrics()
        disk = self.get_disk_usage()
        network = self.get_network_io()
        processes = self.get_process_list()
        sensors = self.get_sensors()
        battery = self.get_battery()
        info = self.get_static_info()
        return {
            "cpu": cpu,
            "memory": memory,
            "disk": disk,
            "network": network,
            "processes": processes,
            "sensors": sensors,
            "battery": battery,
            "static_info": info,
            "boot_time": self.get_boot_time(),
        }
