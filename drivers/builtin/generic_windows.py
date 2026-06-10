from typing import Any, override

import psutil

from backend.interfaces.caps import (
    BatteryMetrics,
    CPUMetrics,
    GPUMetrics,
    NetworkMetrics,
    ProcessInfo,
    RAMMetrics,
    SensorReading,
    StorageMetrics,
    SystemCapabilities,
    SystemMetrics,
)
from backend.interfaces.enums import Permission
from backend.interfaces.plugins import BaseDriver, PluginMeta


try:
    import GPUtil  # type: ignore  # noqa: PGH003
except ImportError:
    GPUtil = None


METADATA: PluginMeta = {
    "name": "Built-in Windows Driver",
    "author": "Core Team",
    "version": "1.0",
    "permissions": [Permission.SYSTEM_READ, Permission.PROCESS_KILL],
    "compatible": [
        "sys.platform EQ 'win32' -> FULL",
    ],
}


class WindowsDriver(BaseDriver):
    @override
    def get_capabilities(self) -> SystemCapabilities:
        return SystemCapabilities(
            has_process_list=True,
            has_gpu=GPUtil is not None,
            has_storage=True,
            has_network=True,
            has_sensors=True,
            has_battery=True,
        )

    @override
    def fetch_metrics(self) -> SystemMetrics:
        cpu = CPUMetrics(
            physical_cores=psutil.cpu_count(logical=False),
            logical_cores=psutil.cpu_count(logical=True),
            usage_percent=psutil.cpu_percent(interval=None),
        )

        mem = psutil.virtual_memory()
        ram = RAMMetrics(
            total_bytes=mem.total,
            used_bytes=mem.used,
            available_bytes=mem.available,
            percent=mem.percent,
        )

        processes: list[ProcessInfo] = []
        for proc in psutil.process_iter(
            ["pid", "name", "cpu_percent", "memory_info", "status", "username"]
        ):
            try:
                pinfo = proc.info
                mi = pinfo["memory_info"]
                processes.append(
                    ProcessInfo(
                        pid=pinfo["pid"],
                        name=pinfo["name"] or "",
                        cpu_percent=pinfo["cpu_percent"] or 0.0,
                        memory_rss=mi.rss if mi else 0,
                        status=pinfo["status"] or "",
                        username=pinfo.get("username"),
                    )
                )
            except psutil.NoSuchProcess, psutil.AccessDenied:
                continue

        storage: list[StorageMetrics] = []
        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
                storage.append(
                    StorageMetrics(
                        mount_point=part.mountpoint,
                        total_bytes=usage.total,
                        used_bytes=usage.used,
                        free_bytes=usage.free,
                        percent=usage.percent,
                    )
                )
            except PermissionError:
                continue

        net_io = psutil.net_io_counters()
        network = [
            NetworkMetrics(
                bytes_sent=net_io.bytes_sent,
                bytes_recv=net_io.bytes_recv,
                packets_sent=net_io.packets_sent,
                packets_recv=net_io.packets_recv,
            )
        ]

        gpu: list[GPUMetrics] | None = None
        if GPUtil is not None:
            try:
                gpus = GPUtil.getGPUs()
                gpu = [
                    GPUMetrics(
                        name=g.name,
                        usage_percent=g.load * 100,
                        memory_total=int(g.memoryTotal * 1024 * 1024),
                        memory_used=int(g.memoryUsed * 1024 * 1024),
                    )
                    for g in gpus
                ]
            except Exception:
                pass

        sensors: list[SensorReading] = []
        try:
            for name, entries in psutil.sensors_temperatures().items():
                for entry in entries:
                    sensors.append(
                        SensorReading(
                            name=f"{name}_{entry.label or 'unknown'}",
                            value=entry.current,
                        )
                    )
        except Exception:
            pass

        battery: BatteryMetrics | None = None
        try:
            sb = psutil.sensors_battery()
            if sb is not None:
                battery = BatteryMetrics(
                    percent=sb.percent,
                    power_plugged=sb.power_plugged,
                    seconds_left=sb.secsleft if sb.secsleft != -1 else None,
                )
        except Exception:
            pass

        return SystemMetrics(
            cpu=cpu,
            ram=ram,
            processes=processes,
            storage=storage,
            network=network,
            gpu=gpu,
            sensors=sensors,
            battery=battery,
        )

    @override
    def manage_process(self, pid: int, action: str, **kwargs: Any) -> bool:
        if action == "kill":
            try:
                proc = psutil.Process(pid)
                proc.kill()
                return True
            except psutil.NoSuchProcess, psutil.AccessDenied:
                return False
        return False


DRIVER = WindowsDriver
