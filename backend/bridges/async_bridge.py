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

    def __init__(
        self, driver: BaseDriver, permissions: set[Permission] | None = None
    ) -> None:
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

        return any(PermissionHierarchy.grants(p, required) for p in self._permissions)

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
            return {
                "cpu_percent": 0.0,
                "per_core": [],
                "frequency": None,
                "physical_cores": 0,
                "logical_cores": 0,
            }
        from backend.interfaces.contexts import DriverContext
        from backend.interfaces.sentinels import Unavailable

        loop = asyncio.get_running_loop()
        ctx = DriverContext()
        cpu_data = await loop.run_in_executor(None, self._driver.tick_cpu, ctx)
        if isinstance(cpu_data, Unavailable):
            return {
                "cpu_percent": 0.0,
                "per_core": [],
                "frequency": None,
                "physical_cores": 0,
                "logical_cores": 0,
            }
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

    async def get_memory_metrics(self) -> dict:
        """Return memory metrics as a flat dict."""
        from backend.interfaces.enums import Permission

        if not self._check(Permission.MEMORY_READ):
            return {
                "total": 0,
                "used": 0,
                "available": 0,
                "free": 0,
                "cached": 0,
                "percent": 0.0,
            }
        from backend.interfaces.contexts import DriverContext
        from backend.interfaces.sentinels import Unavailable

        loop = asyncio.get_running_loop()
        ctx = DriverContext()
        mem_data = await loop.run_in_executor(None, self._driver.tick_memory, ctx)
        if isinstance(mem_data, Unavailable):
            return {
                "total": 0,
                "used": 0,
                "available": 0,
                "free": 0,
                "cached": 0,
                "percent": 0.0,
            }
        return memory_collection_to_dict(mem_data)

    async def get_disk_usage(self, path: str = "/") -> dict:
        """Return disk usage for *path* as a flat dict."""
        from backend.interfaces.enums import Permission

        if not self._check(Permission.DISK_READ):
            return {"total": 0, "used": 0, "free": 0, "percent": 0.0}
        from backend.interfaces.contexts import DriverContext
        from backend.interfaces.sentinels import Unavailable

        loop = asyncio.get_running_loop()
        ctx = DriverContext()
        disk_data = await loop.run_in_executor(None, self._driver.tick_disk, ctx)
        if isinstance(disk_data, Unavailable):
            return {"total": 0, "used": 0, "free": 0, "percent": 0.0}
        return disk_collection_to_dict(disk_data, mount_point=path)

    async def get_network_io(self) -> dict:
        """Return aggregate network IO as a flat dict."""
        from backend.interfaces.enums import Permission

        if not self._check(Permission.NETWORK_READ):
            return {"bytes_sent": 0, "bytes_recv": 0}
        from backend.interfaces.contexts import DriverContext
        from backend.interfaces.sentinels import Unavailable

        loop = asyncio.get_running_loop()
        ctx = DriverContext()
        net_data = await loop.run_in_executor(None, self._driver.tick_network, ctx)
        if isinstance(net_data, Unavailable):
            return {"bytes_sent": 0, "bytes_recv": 0}
        return network_collection_to_dict(net_data)

    async def get_process_list(self) -> list[dict]:
        """Return process list as a list of flat dicts."""
        from backend.interfaces.enums import Permission

        if not self._check(Permission.PROCESSES_READ):
            return []
        from backend.interfaces.contexts import DriverContext
        from backend.interfaces.sentinels import Unavailable

        loop = asyncio.get_running_loop()
        ctx = DriverContext()
        proc_data = await loop.run_in_executor(None, self._driver.tick_processes, ctx)
        if isinstance(proc_data, Unavailable):
            return []
        return process_collection_to_dict(proc_data)

    async def get_sensors(self) -> dict:
        """Return sensor temperatures as a dict."""
        from backend.interfaces.enums import Permission

        if not self._check(Permission.SENSORS_READ):
            return {"temperatures": {}}
        from backend.interfaces.contexts import DriverContext
        from backend.interfaces.sentinels import Unavailable

        loop = asyncio.get_running_loop()
        ctx = DriverContext()
        sensor_data = await loop.run_in_executor(None, self._driver.tick_sensors, ctx)
        if isinstance(sensor_data, Unavailable):
            return {"temperatures": {}}
        return sensor_collection_to_dict(sensor_data)

    async def get_battery(self) -> dict:
        """Return battery info as a flat dict."""
        from backend.interfaces.enums import Permission

        if not self._check(Permission.BATTERY_READ):
            return {"percent": 0.0, "power_plugged": None, "seconds_left": None}
        from backend.interfaces.contexts import DriverContext
        from backend.interfaces.sentinels import Unavailable

        loop = asyncio.get_running_loop()
        ctx = DriverContext()
        battery_data = await loop.run_in_executor(None, self._driver.tick_battery, ctx)
        if isinstance(battery_data, Unavailable):
            return {"percent": 0.0, "power_plugged": None, "seconds_left": None}
        return battery_collection_to_dict(battery_data)

    async def get_static_info(self) -> dict:
        """Return static system info as a nested dict."""
        from backend.interfaces.enums import Permission

        if not self._check(Permission.SYSTEM_READ):
            return {}
        info = self._driver.get_static_info()
        if info is None:
            return {}
        from backend.interfaces.caps import dump_static_info as _dump

        return _dump(info)

    async def get_boot_time(self) -> float:
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
            return {
                "cpu": {},
                "memory": {},
                "disk": {},
                "network": {},
                "processes": [],
                "sensors": {},
                "battery": {},
            }

        u = Unavailable

        cpu: dict
        if self._check(Permission.CPU_READ) and not isinstance(snap.cpu, u):
            static = self._driver.get_static_info()
            if static is not None:
                raw_cores = static.cpu.physical_cores
                raw_threads = static.cpu.logical_cores
                cores = raw_cores if isinstance(raw_cores, int) else 0
                threads = raw_threads if isinstance(raw_threads, int) else 0
            else:
                cores = threads = 0
            cpu = cpu_collection_to_dict(
                snap.cpu, static_cores=cores, static_threads=threads
            )
        else:
            cpu = {
                "cpu_percent": 0.0,
                "per_core": [],
                "frequency": None,
                "physical_cores": 0,
                "logical_cores": 0,
            }

        memory: dict
        if self._check(Permission.MEMORY_READ) and not isinstance(snap.memory, u):
            memory = memory_collection_to_dict(snap.memory)
        else:
            memory = {
                "total": 0,
                "used": 0,
                "available": 0,
                "free": 0,
                "cached": 0,
                "percent": 0.0,
            }

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
            "cpu": cpu,
            "memory": memory,
            "disk": disk,
            "network": network,
            "processes": processes,
            "sensors": sensors,
            "battery": battery,
        }
