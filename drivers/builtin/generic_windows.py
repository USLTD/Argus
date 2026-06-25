import time
from datetime import datetime
from typing import Any, override

import getpass
import platform
import socket

import psutil

from backend.interfaces.caps import (
    BatteryCapabilities,
    BatteryMetric,
    CpuCapabilities,
    CPUMetric,
    DriverInfo,
    GpuCapabilities,
    GPUMetric,
    MemoryMetric,
    MetricMetadata,
    MetricsCollection,
    NetworkCapabilities,
    NetworkMetric,
    ProcessCapabilities,
    ProcessMetric,
    SensorCapabilities,
    SensorMetric,
    StaticSystemInfo,
    StorageCapabilities,
    StorageMetric,
    SystemCapabilities,
)
from backend.interfaces.contexts import DriverContext
from backend.interfaces.sentinels import Unavailable
from backend.interfaces.plugins import BaseDriver, PluginMeta


try:
    import GPUtil  # type: ignore  # noqa: PGH003
except ImportError:
    GPUtil = None

try:
    import cpuinfo  # type: ignore  # noqa: PGH003
except ImportError:
    cpuinfo = None  # type: ignore[assignment]

try:
    import wmi  # type: ignore  # noqa: PGH003
except ImportError:
    wmi = None  # type: ignore[assignment]


METADATA: PluginMeta = {
    "name": "Built-in Windows Driver",
    "author": "Core Team",
    "version": "1.0",
    "compatible": [
        "sys.platform EQ 'win32' -> FULL",
    ],
}


class WindowsDriver(BaseDriver):
    @override
    def get_capabilities(self) -> SystemCapabilities:
        return SystemCapabilities(
            cpu=CpuCapabilities(present=True, frequency=True, core_count=True),
            gpu=GpuCapabilities(present=GPUtil is not None, detail=GPUtil is not None),
            process=ProcessCapabilities(list=True, detail=True),
            storage=StorageCapabilities(present=True, disk_io=True),
            network=NetworkCapabilities(present=True, bandwidth=True),
            sensors=SensorCapabilities(present=True),
            battery=BatteryCapabilities(present=True),
            driver=DriverInfo(name="Built-in Windows Driver", version="1.0", platform="win32"),
        )

    @override
    def tick_cpu(self, ctx: DriverContext) -> MetricsCollection[CPUMetric] | Unavailable:
        try:
            freq = psutil.cpu_freq()
            return MetricsCollection[CPUMetric](
                metadata=MetricMetadata(collected_at=time.time()),
                metrics=[
                    CPUMetric(core_id=None, usage_percent=psutil.cpu_percent(), frequency_mhz=freq.current if freq else None),
                    *[CPUMetric(core_id=i, usage_percent=p) for i, p in enumerate(psutil.cpu_percent(percpu=True))],
                ],
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
            metrics: list[ProcessMetric] = []
            for proc in psutil.process_iter(
                ["pid", "name", "cpu_percent", "memory_info", "status", "username"]
            ):
                try:
                    pinfo = proc.info
                    mi = pinfo["memory_info"]
                    metrics.append(
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
                metrics=metrics,
            )
        except Exception as e:
            return Unavailable("error", str(e))

    @override
    def tick_disk(self, ctx: DriverContext) -> MetricsCollection[StorageMetric] | Unavailable:
        try:
            metrics: list[StorageMetric] = []
            for part in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    metrics.append(
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
                metrics=metrics,
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
            return MetricsCollection[GPUMetric](
                metadata=MetricMetadata(collected_at=time.time()),
                metrics=[
                    GPUMetric(
                        name=g.name,
                        usage_percent=g.load * 100,
                        memory_total=int(g.memoryTotal * 1024 * 1024),
                        memory_used=int(g.memoryUsed * 1024 * 1024),
                    )
                    for g in gpus
                ],
            )
        except Exception as e:
            return Unavailable("error", str(e))

    @override
    def tick_sensors(self, ctx: DriverContext) -> MetricsCollection[SensorMetric] | Unavailable:
        try:
            metrics: list[SensorMetric] = []
            for name, entries in psutil.sensors_temperatures().items():
                for entry in entries:
                    metrics.append(
                        SensorMetric(
                            name=f"{name}_{entry.label or 'unknown'}",
                            value=entry.current,
                        )
                    )
            return MetricsCollection[SensorMetric](
                metadata=MetricMetadata(collected_at=time.time()),
                metrics=metrics,
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
    def get_static_info(self) -> StaticSystemInfo:
        os_name = platform.system()
        os_version = platform.version()
        hostname = socket.gethostname()
        username = getpass.getuser()

        cpu_brand: str = "Unknown"
        if cpuinfo is not None:
            try:
                cpu_info_raw = cpuinfo.get_cpu_info()
                cpu_brand = cpu_info_raw.get("brand_raw", "Unknown")
            except Exception:
                cpu_brand = platform.processor() or "Unknown"
        else:
            cpu_brand = platform.processor() or "Unknown"

        cpu_phys = psutil.cpu_count(logical=False) or 0
        cpu_log = psutil.cpu_count(logical=True) or 0

        cpu_freq = psutil.cpu_freq()
        cpu_freq_mhz: float | None = cpu_freq.current if cpu_freq is not None else None

        total_ram = psutil.virtual_memory().total
        arch = platform.architecture()[0]
        py_ver = platform.python_version()
        boot_time = datetime.fromtimestamp(psutil.boot_time()).isoformat()

        gpu_name: str | None = None
        gpu_driver: str | None = None
        gpu_vram: int | None = None
        motherboard_manufacturer: str | None = None
        motherboard_model: str | None = None
        bios_version: str | None = None

        if wmi is not None:
            try:
                wmi_conn = wmi.WMI()
                for video in wmi_conn.Win32_VideoController():
                    gpu_name = video.Name
                    gpu_driver = video.DriverVersion
                    if video.AdapterRAM is not None:
                        gpu_vram = int(video.AdapterRAM)
                    break
                for board in wmi_conn.Win32_BaseBoard():
                    motherboard_manufacturer = board.Manufacturer
                    motherboard_model = board.Product
                    break
                for bios in wmi_conn.Win32_BIOS():
                    bios_version = bios.SMBIOSBIOSVersion
                    break
            except Exception:
                pass

        return StaticSystemInfo(
            os_name=os_name,
            os_version=os_version,
            hostname=hostname,
            username=username,
            cpu_brand=cpu_brand,
            cpu_physical_cores=cpu_phys,
            cpu_logical_cores=cpu_log,
            cpu_frequency_mhz=cpu_freq_mhz,
            gpu_name=gpu_name,
            gpu_driver=gpu_driver,
            gpu_vram_bytes=gpu_vram,
            motherboard_manufacturer=motherboard_manufacturer,
            motherboard_model=motherboard_model,
            bios_version=bios_version,
            total_ram_bytes=total_ram,
            architecture=arch,
            python_version=py_ver,
            boot_time=boot_time,
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
