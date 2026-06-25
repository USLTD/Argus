"""Asyncio-friendly driver bridge with NO PyQt6 dependency.

Each get_*() method calls await self.tick_all() to refresh data
in a thread executor, keeping the event loop unblocked.
"""

from __future__ import annotations

import asyncio
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


class AsyncBridge:
    """Async bridge wrapping a BaseDriver.

    All blocking driver calls run in a thread executor so the
    event loop is never blocked.
    """

    def __init__(self, driver: BaseDriver, permissions: set[Permission] | None = None) -> None:
        self._driver = driver
        self._permissions = permissions
        self._snapshot: TickSnapshot | None = None
        self._poll_task: asyncio.Task[None] | None = None

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

    async def tick_all(self) -> None:
        """Refresh all metrics from the driver in a thread executor."""
        from backend.interfaces.contexts import DriverContext

        loop = asyncio.get_running_loop()
        ctx = DriverContext()
        self._snapshot = await loop.run_in_executor(None, self._driver.tick, ctx)

    async def start_polling(self, interval: float = 2.0) -> None:
        """Start background auto-refresh every *interval* seconds."""

        if self._poll_task is not None:
            return

        async def _run() -> None:
            while True:
                try:
                    await self.tick_all()
                except Exception:
                    pass  # keep polling even on transient errors
                await asyncio.sleep(interval)

        self._poll_task = asyncio.create_task(_run())

    async def stop_polling(self) -> None:
        """Cancel the background polling task."""
        if self._poll_task is not None:
            self._poll_task.cancel()
            self._poll_task = None

    @property
    def snapshot(self) -> TickSnapshot | None:
        return self._snapshot

    # ── per-subsystem getters ──────────────────────────────────────

    async def get_cpu_metrics(self) -> dict:
        """Return CPU metrics as a flat dict."""
        from backend.interfaces.enums import Permission
        if not self._check(Permission.CPU_READ):
            return {"cpu_percent": 0.0, "per_core": [], "frequency": None, "physical_cores": 0, "logical_cores": 0}
        await self.tick_all()
        from backend.interfaces.sentinels import Unavailable

        snap = self._snapshot
        if snap is None or isinstance(snap.cpu, Unavailable):
            return {"cpu_percent": 0.0, "per_core": [], "frequency": None, "physical_cores": 0, "logical_cores": 0}
        static = self._driver.get_static_info()
        return cpu_collection_to_dict(
            snap.cpu,
            static_cores=getattr(static, "cpu_physical_cores", 0) if static else 0,
            static_threads=getattr(static, "cpu_logical_cores", 0) if static else 0,
        )

    async def get_memory_metrics(self) -> dict:
        """Return memory metrics as a flat dict."""
        from backend.interfaces.enums import Permission
        if not self._check(Permission.MEMORY_READ):
            return {"total": 0, "used": 0, "available": 0, "free": 0, "cached": 0, "percent": 0.0}
        await self.tick_all()
        from backend.interfaces.sentinels import Unavailable

        snap = self._snapshot
        if snap is None or isinstance(snap.memory, Unavailable):
            return {"total": 0, "used": 0, "available": 0, "free": 0, "cached": 0, "percent": 0.0}
        return memory_collection_to_dict(snap.memory)

    async def get_disk_usage(self, path: str = "/") -> dict:
        """Return disk usage for *path* as a flat dict."""
        from backend.interfaces.enums import Permission
        if not self._check(Permission.DISK_READ):
            return {"total": 0, "used": 0, "free": 0, "percent": 0.0}
        await self.tick_all()
        from backend.interfaces.sentinels import Unavailable

        snap = self._snapshot
        if snap is None or isinstance(snap.disk, Unavailable):
            return {"total": 0, "used": 0, "free": 0, "percent": 0.0}
        return disk_collection_to_dict(snap.disk, mount_point=path)

    async def get_network_io(self) -> dict:
        """Return aggregate network IO as a flat dict."""
        from backend.interfaces.enums import Permission
        if not self._check(Permission.NETWORK_READ):
            return {"bytes_sent": 0, "bytes_recv": 0}
        await self.tick_all()
        from backend.interfaces.sentinels import Unavailable

        snap = self._snapshot
        if snap is None or isinstance(snap.network, Unavailable):
            return {"bytes_sent": 0, "bytes_recv": 0}
        return network_collection_to_dict(snap.network)

    async def get_process_list(self) -> list[dict]:
        """Return process list as a list of flat dicts."""
        from backend.interfaces.enums import Permission
        if not self._check(Permission.PROCESSES_READ):
            return []
        await self.tick_all()
        from backend.interfaces.sentinels import Unavailable

        snap = self._snapshot
        if snap is None or isinstance(snap.processes, Unavailable):
            return []
        return process_collection_to_dict(snap.processes)

    async def get_sensors(self) -> dict:
        """Return sensor temperatures as a dict."""
        from backend.interfaces.enums import Permission
        if not self._check(Permission.SENSORS_READ):
            return {"temperatures": {}}
        await self.tick_all()
        from backend.interfaces.sentinels import Unavailable

        snap = self._snapshot
        if snap is None or isinstance(snap.sensors, Unavailable):
            return {"temperatures": {}}
        return sensor_collection_to_dict(snap.sensors)

    async def get_battery(self) -> dict:
        """Return battery info as a flat dict."""
        from backend.interfaces.enums import Permission
        if not self._check(Permission.BATTERY_READ):
            return {"percent": 0.0, "power_plugged": None, "seconds_left": None}
        await self.tick_all()
        from backend.interfaces.sentinels import Unavailable

        snap = self._snapshot
        if snap is None or isinstance(snap.battery, Unavailable):
            return {"percent": 0.0, "power_plugged": None, "seconds_left": None}
        return battery_collection_to_dict(snap.battery)

    async def get_static_info(self) -> dict:
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

    async def get_boot_time(self) -> float:
        """Return boot time timestamp."""
        from backend.interfaces.enums import Permission
        if not self._check(Permission.SYSTEM_READ):
            return 0.0
        info = self._driver.get_static_info()
        if info is None:
            return 0.0
        return getattr(info, "boot_time", 0.0)

    async def terminate_process(self, pid: int) -> bool:
        """Ask the driver to terminate *pid* gracefully."""
        from backend.interfaces.enums import Permission
        if not self._check(Permission.PROCESSES_WRITE):
            return False
        try:
            return self._driver.manage_process(pid, "terminate")
        except Exception:
            return False

    async def kill_process(self, pid: int) -> bool:
        """Ask the driver to force-kill *pid*."""
        from backend.interfaces.enums import Permission
        if not self._check(Permission.PROCESSES_EXECUTE):
            return False
        try:
            return self._driver.manage_process(pid, "kill")
        except Exception:
            return False

    async def get_all(self) -> dict:
        """Return ALL metrics as one dict from a single tick."""
        await self.tick_all()
        from backend.interfaces.enums import Permission
        from backend.interfaces.sentinels import Unavailable

        snap = self._snapshot
        if snap is None:
            return {"cpu": {}, "memory": {}, "disk": {}, "network": {}, "processes": [], "sensors": {}, "battery": {}}

        u = Unavailable

        cpu: dict
        if self._check(Permission.CPU_READ) and not isinstance(snap.cpu, u):
            cpu = cpu_collection_to_dict(snap.cpu, 0, 0)
        else:
            cpu = {"cpu_percent": 0.0, "per_core": [], "frequency": None, "physical_cores": 0, "logical_cores": 0}

        memory: dict
        if self._check(Permission.MEMORY_READ) and not isinstance(snap.memory, u):
            memory = memory_collection_to_dict(snap.memory)
        else:
            memory = {"total": 0, "used": 0, "available": 0, "free": 0, "cached": 0, "percent": 0.0}

        disk: dict
        if self._check(Permission.DISK_READ) and not isinstance(snap.disk, u):
            disk = disk_collection_to_dict(snap.disk)
        else:
            disk = {"total": 0, "used": 0, "free": 0, "percent": 0.0}

        network: dict
        if self._check(Permission.NETWORK_READ) and not isinstance(snap.network, u):
            network = network_collection_to_dict(snap.network)
        else:
            network = {"bytes_sent": 0, "bytes_recv": 0}

        processes: list
        if self._check(Permission.PROCESSES_READ) and not isinstance(snap.processes, u):
            processes = process_collection_to_dict(snap.processes)
        else:
            processes = []

        sensors: dict
        if self._check(Permission.SENSORS_READ) and not isinstance(snap.sensors, u):
            sensors = sensor_collection_to_dict(snap.sensors)
        else:
            sensors = {"temperatures": {}}

        battery: dict
        if self._check(Permission.BATTERY_READ) and not isinstance(snap.battery, u):
            battery = battery_collection_to_dict(snap.battery)
        else:
            battery = {"percent": 0.0, "power_plugged": None, "seconds_left": None}

        return {
            "cpu": cpu, "memory": memory, "disk": disk, "network": network,
            "processes": processes, "sensors": sensors, "battery": battery,
        }
