"""Synchronous driver bridge with NO PyQt6 dependency.

Used by Textual TUI and CLI tools. Every call to a get_*() method
re-fetches from the driver via tick_all() to ensure fresh data.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

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
        self._engine: object | None = None
        self._snapshot: TickSnapshot | None = None
        self._last_tick: float = 0.0

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
        """Refresh all metrics from the driver (idempotent: no-op if ticked within 50ms)."""
        now = time.monotonic()
        if now - self._last_tick < 0.05:
            return
        from backend.interfaces.contexts import DriverContext

        ctx = DriverContext()
        self._snapshot = self._driver.tick(ctx)
        self._last_tick = now

    # ── per-subsystem getters ──────────────────────────────────────

    def get_cpu_metrics(self) -> dict:
        """Return CPU metrics as a flat dict."""
        from backend.interfaces.enums import Permission
        if not self._check(Permission.CPU_READ):
            return {"cpu_percent": 0.0, "per_core": [], "frequency": None, "physical_cores": 0, "logical_cores": 0}
        from backend.interfaces.contexts import DriverContext
        from backend.interfaces.sentinels import Unavailable

        cpu_data = self._driver.tick_cpu(DriverContext())
        if isinstance(cpu_data, Unavailable):
            return {"cpu_percent": 0.0, "per_core": [], "frequency": None, "physical_cores": 0, "logical_cores": 0}
        static = self._driver.get_static_info()
        if static is not None:
            raw_cores = static.cpu.physical_cores
            raw_threads = static.cpu.logical_cores
            cores = raw_cores if isinstance(raw_cores, int) else 0
            threads = raw_threads if isinstance(raw_threads, int) else 0
        else:
            cores = threads = 0
        return cpu_collection_to_dict(
            cpu_data,
            static_cores=cores,
            static_threads=threads,
        )

    def get_memory_metrics(self) -> dict:
        """Return memory metrics as a flat dict."""
        from backend.interfaces.enums import Permission
        if not self._check(Permission.MEMORY_READ):
            return {"total": 0, "used": 0, "available": 0, "free": 0, "cached": 0, "percent": 0.0}
        from backend.interfaces.contexts import DriverContext
        from backend.interfaces.sentinels import Unavailable

        mem_data = self._driver.tick_memory(DriverContext())
        if isinstance(mem_data, Unavailable):
            return {"total": 0, "used": 0, "available": 0, "free": 0, "cached": 0, "percent": 0.0}
        return memory_collection_to_dict(mem_data)

    def get_disk_usage(self, path: str = "/") -> dict:
        """Return disk usage for *path* as a flat dict."""
        from backend.interfaces.enums import Permission
        if not self._check(Permission.DISK_READ):
            return {"total": 0, "used": 0, "free": 0, "percent": 0.0}
        from backend.interfaces.contexts import DriverContext
        from backend.interfaces.sentinels import Unavailable

        disk_data = self._driver.tick_disk(DriverContext())
        if isinstance(disk_data, Unavailable):
            return {"total": 0, "used": 0, "free": 0, "percent": 0.0}
        return disk_collection_to_dict(disk_data, mount_point=path)

    def get_network_io(self) -> dict:
        """Return aggregate network IO as a flat dict."""
        from backend.interfaces.enums import Permission
        if not self._check(Permission.NETWORK_READ):
            return {"bytes_sent": 0, "bytes_recv": 0}
        from backend.interfaces.contexts import DriverContext
        from backend.interfaces.sentinels import Unavailable

        net_data = self._driver.tick_network(DriverContext())
        if isinstance(net_data, Unavailable):
            return {"bytes_sent": 0, "bytes_recv": 0}
        return network_collection_to_dict(net_data)

    def get_process_list(self) -> list[dict]:
        """Return process list as a list of flat dicts."""
        from backend.interfaces.enums import Permission
        if not self._check(Permission.PROCESSES_READ):
            return []
        from backend.interfaces.contexts import DriverContext
        from backend.interfaces.sentinels import Unavailable

        proc_data = self._driver.tick_processes(DriverContext())
        if isinstance(proc_data, Unavailable):
            return []
        return process_collection_to_dict(proc_data)

    def get_sensors(self) -> dict:
        """Return sensor temperatures as a dict of name -> list of values."""
        from backend.interfaces.enums import Permission
        if not self._check(Permission.SENSORS_READ):
            return {"temperatures": {}}
        from backend.interfaces.contexts import DriverContext
        from backend.interfaces.sentinels import Unavailable

        sensor_data = self._driver.tick_sensors(DriverContext())
        if isinstance(sensor_data, Unavailable):
            return {"temperatures": {}}
        return sensor_collection_to_dict(sensor_data)

    def get_battery(self) -> dict:
        """Return battery info as a flat dict."""
        from backend.interfaces.enums import Permission
        if not self._check(Permission.BATTERY_READ):
            return {"percent": 0.0, "power_plugged": None, "seconds_left": None}
        from backend.interfaces.contexts import DriverContext
        from backend.interfaces.sentinels import Unavailable

        battery_data = self._driver.tick_battery(DriverContext())
        if isinstance(battery_data, Unavailable):
            return {"percent": 0.0, "power_plugged": None, "seconds_left": None}
        return battery_collection_to_dict(battery_data)

    def get_static_info(self) -> dict:
        """Return static system info as a nested dict."""
        from backend.interfaces.enums import Permission
        if not self._check(Permission.SYSTEM_READ):
            return {}
        info = self._driver.get_static_info()
        if info is None:
            return {}
        from backend.interfaces.caps import dump_static_info as _dump
        return _dump(info)

    def get_boot_time(self) -> float:
        """Return boot time as a Unix timestamp."""
        from backend.interfaces.enums import Permission
        if not self._check(Permission.SYSTEM_READ):
            return 0.0
        info = self._driver.get_static_info()
        if info is None:
            return 0.0
        from backend.interfaces.caps import UnavailableInfo
        from datetime import datetime
        boot_time_val = info.system.boot_time
        if isinstance(boot_time_val, UnavailableInfo):
            return 0.0
        return datetime.fromisoformat(boot_time_val).timestamp()

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

    # ── config read/write ───────────────────────────────────────────

    def read_config(self) -> dict[str, Any]:
        """Read the full config from the engine."""
        if self._engine is None:
            return {}
        return self._engine.get_config()  # type: ignore[union-attr]

    def write_config(self, key: str, value: Any) -> None:
        """Write a single config value through the engine."""
        if self._engine is None:
            raise RuntimeError("SyncBridge has no engine reference")
        self._engine.set_config(key, value)  # type: ignore[union-attr]

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
