from typing import Any, override

import time

import psutil

from backend.interfaces.caps import (
    BatteryMetric,
    CPUMetric,
    GPUMetric,
    MemoryMetric,
    MetricMetadata,
    MetricsCollection,
    NetworkMetric,
    ProcessMetric,
    SensorMetric,
    StorageMetric,
    SystemCapabilities,
)
from backend.interfaces.contexts import DriverContext
from backend.interfaces.plugins import BaseDriver, PluginMeta
from backend.interfaces.sentinels import Unavailable, TickSnapshot


try:
    import GPUtil  # type: ignore  # noqa: PGH003
except ImportError:
    GPUtil = None


METADATA: PluginMeta = {
    "name": "Generic Linux Driver",
    "author": "Core Team",
    "version": "1.0",
    "compatible": [
        "sys.platform EQ 'linux' -> HIGH",
    ],
}


class LinuxDriver(BaseDriver):
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
    def tick_cpu(self, ctx: DriverContext) -> MetricsCollection[CPUMetric] | Unavailable:
        try:
            freq = psutil.cpu_freq()
            aggregate = CPUMetric(
                core_id=None,
                usage_percent=psutil.cpu_percent(),
                frequency_mhz=freq.current if freq else None,
            )
            per_core = [
                CPUMetric(core_id=i, usage_percent=p)
                for i, p in enumerate(psutil.cpu_percent(percpu=True))
            ]
            return MetricsCollection[CPUMetric](
                metadata=MetricMetadata(collected_at=time.time()),
                metrics=[aggregate, *per_core],
            )
        except Exception as e:
            return Unavailable("error", str(e))

    @override
    def tick_memory(self, ctx: DriverContext) -> MetricsCollection[MemoryMetric] | Unavailable:
        try:
            mem = psutil.virtual_memory()
            return MetricsCollection[MemoryMetric](
                metadata=MetricMetadata(collected_at=time.time()),
                metrics=[
                    MemoryMetric(
                        total_bytes=mem.total,
                        used_bytes=mem.used,
                        available_bytes=mem.available,
                        percent=mem.percent,
                    )
                ],
            )
        except Exception as e:
            return Unavailable("error", str(e))

    @override
    def tick_processes(self, ctx: DriverContext) -> MetricsCollection[ProcessMetric] | Unavailable:
        try:
            processes: list[ProcessMetric] = []
            for proc in psutil.process_iter(
                ["pid", "name", "cpu_percent", "memory_info", "status", "username"]
            ):
                try:
                    pinfo = proc.info
                    mi = pinfo["memory_info"]
                    processes.append(
                        ProcessMetric(
                            pid=pinfo["pid"],
                            name=pinfo["name"] or "",
                            cpu_percent=pinfo["cpu_percent"] or 0.0,
                            memory_rss=mi.rss if mi else 0,
                            status=pinfo["status"] or "",
                            username=pinfo.get("username"),
                        )
                    )
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return MetricsCollection[ProcessMetric](
                metadata=MetricMetadata(collected_at=time.time()),
                metrics=processes,
            )
        except Exception as e:
            return Unavailable("error", str(e))

    @override
    def tick_disk(self, ctx: DriverContext) -> MetricsCollection[StorageMetric] | Unavailable:
        try:
            storage: list[StorageMetric] = []
            for part in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    storage.append(
                        StorageMetric(
                            mount_point=part.mountpoint,
                            total_bytes=usage.total,
                            used_bytes=usage.used,
                            free_bytes=usage.free,
                            percent=usage.percent,
                        )
                    )
                except PermissionError:
                    continue
            return MetricsCollection[StorageMetric](
                metadata=MetricMetadata(collected_at=time.time()),
                metrics=storage,
            )
        except Exception as e:
            return Unavailable("error", str(e))

    @override
    def tick_network(self, ctx: DriverContext) -> MetricsCollection[NetworkMetric] | Unavailable:
        try:
            net_io = psutil.net_io_counters()
            return MetricsCollection[NetworkMetric](
                metadata=MetricMetadata(collected_at=time.time()),
                metrics=[
                    NetworkMetric(
                        bytes_sent=net_io.bytes_sent,
                        bytes_recv=net_io.bytes_recv,
                        packets_sent=net_io.packets_sent,
                        packets_recv=net_io.packets_recv,
                    )
                ],
            )
        except Exception as e:
            return Unavailable("error", str(e))

    @override
    def tick_gpu(self, ctx: DriverContext) -> MetricsCollection[GPUMetric] | Unavailable:
        if GPUtil is None:
            return Unavailable("unsupported", "GPUtil not installed")
        try:
            gpus = GPUtil.getGPUs()
            metrics = [
                GPUMetric(
                    name=g.name,
                    usage_percent=g.load * 100,
                    memory_total=int(g.memoryTotal * 1024 * 1024),
                    memory_used=int(g.memoryUsed * 1024 * 1024),
                )
                for g in gpus
            ]
            return MetricsCollection[GPUMetric](
                metadata=MetricMetadata(collected_at=time.time()),
                metrics=metrics,
            )
        except Exception as e:
            return Unavailable("error", str(e))

    @override
    def tick_sensors(self, ctx: DriverContext) -> MetricsCollection[SensorMetric] | Unavailable:
        try:
            sensors: list[SensorMetric] = []
            for name, entries in psutil.sensors_temperatures().items():
                for entry in entries:
                    sensors.append(
                        SensorMetric(
                            name=f"{name}_{entry.label or 'unknown'}",
                            value=entry.current,
                        )
                    )
            return MetricsCollection[SensorMetric](
                metadata=MetricMetadata(collected_at=time.time()),
                metrics=sensors,
            )
        except Exception as e:
            return Unavailable("error", str(e))

    @override
    def tick_battery(self, ctx: DriverContext) -> MetricsCollection[BatteryMetric] | Unavailable:
        try:
            sb = psutil.sensors_battery()
            if sb is None:
                return Unavailable("unsupported", "No battery detected")
            return MetricsCollection[BatteryMetric](
                metadata=MetricMetadata(collected_at=time.time()),
                metrics=[
                    BatteryMetric(
                        percent=sb.percent,
                        power_plugged=sb.power_plugged,
                        seconds_left=sb.secsleft if sb.secsleft != -1 else None,
                    )
                ],
            )
        except Exception as e:
            return Unavailable("error", str(e))

    @override
    def manage_process(self, pid: int, action: str, **kwargs: Any) -> bool:
        if action == "kill":
            try:
                proc = psutil.Process(pid)
                proc.kill()
                return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                return False
        return False


DRIVER = LinuxDriver
