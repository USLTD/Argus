import getpass
import platform
import socket
import time
from datetime import datetime
from typing import Any, override

import psutil

from backend.interfaces.caps import (
    BatteryCapabilities,
    BatteryMetric,
    CpuCapabilities,
    CpuInfo,
    CPUMetric,
    DriverInfo,
    GpuCapabilities,
    GpuInfo,
    GPUMetric,
    MemoryInfo,
    MemoryMetric,
    MetricMetadata,
    MetricsCollection,
    MotherboardInfo,
    NetworkCapabilities,
    NetworkInfo,
    NetworkInterfaceInfo,
    NetworkMetric,
    OsInfo,
    ProcessCapabilities,
    ProcessMetric,
    SensorCapabilities,
    SensorMetric,
    StaticSystemInfo,
    StorageCapabilities,
    StorageMetric,
    SystemCapabilities,
    SystemInfo,
    UnavailableInfo,
    UserMetric,
)
from backend.interfaces.contexts import DriverContext
from backend.interfaces.enums import ConfidenceScore
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
            has_gpu=True,
            has_storage=True,
            has_network=True,
            has_sensors=True,
            has_battery=True,
            cpu=CpuCapabilities(present=True, frequency=True, core_count=True),
            gpu=GpuCapabilities(present=True, detail=True),
            process=ProcessCapabilities(list=True, detail=True),
            storage=StorageCapabilities(present=True, disk_io=True),
            network=NetworkCapabilities(present=True, bandwidth=True),
            sensors=SensorCapabilities(present=True),
            battery=BatteryCapabilities(present=True),
            driver=DriverInfo(name="Generic Linux Driver", version="1.0", platform="linux"),
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
                            category=name,
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
    def tick_users(self, ctx: DriverContext) -> MetricsCollection[UserMetric] | Unavailable:  # type: ignore[reportGeneralTypeIssues]  # basedpyright false positive: method exists on BaseDriver at runtime
        try:
            users = psutil.users()
            return MetricsCollection[UserMetric](
                metadata=MetricMetadata(collected_at=time.time()),
                metrics=[
                    UserMetric(
                        name=u.name,
                        terminal=u.terminal,
                        host=u.host,
                        started=u.started,
                    )
                    for u in users
                ],
            )
        except Exception as e:
            return Unavailable("error", str(e))

    @override
    def _collect_static_info(self) -> StaticSystemInfo:
        os_name = platform.system()
        os_version = platform.version()
        hostname = socket.gethostname()
        username = getpass.getuser()

        cpu_brand: str = "Unknown"
        try:
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if line.startswith("model name"):
                        cpu_brand = line.split(":", 1)[1].strip()
                        break
        except Exception:
            cpu_brand = platform.processor() or "Unknown"

        cpu_phys = psutil.cpu_count(logical=False) or 0
        cpu_log = psutil.cpu_count(logical=True) or 0

        cpu_freq = psutil.cpu_freq()
        cpu_freq_mhz: float | None = cpu_freq.current if cpu_freq is not None else None

        total_ram = psutil.virtual_memory().total
        arch = platform.architecture()[0]
        py_ver = platform.python_version()
        boot_time = datetime.fromtimestamp(psutil.boot_time()).isoformat()

        # Motherboard info from sysfs
        mobo_info: dict[str, Any] = {}
        dmi_base = "/sys/class/dmi/id"
        try:
            with open(f"{dmi_base}/sys_vendor") as f:
                mobo_info["manufacturer"] = f.read().strip()
        except Exception:
            pass
        try:
            with open(f"{dmi_base}/product_name") as f:
                mobo_info["model"] = f.read().strip()
        except Exception:
            pass
        try:
            with open(f"{dmi_base}/bios_version") as f:
                mobo_info["bios_version"] = f.read().strip()
        except Exception:
            pass

        # GPU info via GPUtil (may be unavailable)
        gpu_info: dict[str, Any] = {}
        try:
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu_info = {
                    "name": gpus[0].name,
                    "vram_bytes": int(gpus[0].memoryTotal * 1024 * 1024),
                }
        except Exception:
            pass

        # Network interfaces
        network_interfaces: list[NetworkInterfaceInfo] = []
        try:
            _AF_MAP: dict[int, str] = {}
            for _name in ("AF_INET", "AF_INET6", "AF_PACKET", "AF_LINK", "AF_UNIX"):
                _val = getattr(socket, _name, None)
                if _val is not None:
                    _AF_MAP[_val] = _name
            for iface_name, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    family_str = _AF_MAP.get(addr.family, f"AF_UNKNOWN({addr.family})")
                    network_interfaces.append(
                        NetworkInterfaceInfo(
                            name=iface_name,
                            family=family_str,
                            address=addr.address,
                            netmask=addr.netmask,
                            broadcast=addr.broadcast,
                        )
                    )
        except Exception:
            pass

        return StaticSystemInfo(
            cpu=CpuInfo(
                name=cpu_brand,
                physical_cores=cpu_phys,
                logical_cores=cpu_log,
                frequency_mhz=cpu_freq_mhz,
            ),
            gpu=GpuInfo(
                name=gpu_info.get("name") if "name" in gpu_info else UnavailableInfo(reason="unsupported"),
                driver=UnavailableInfo(reason="unsupported"),  # Linux GPUtil doesn't expose driver version
                vram_bytes=gpu_info.get("vram_bytes") if "vram_bytes" in gpu_info else UnavailableInfo(reason="unsupported"),
            ),
            motherboard=MotherboardInfo(
                manufacturer=mobo_info.get("manufacturer") if "manufacturer" in mobo_info else UnavailableInfo(reason="unsupported"),
                model=mobo_info.get("model") if "model" in mobo_info else UnavailableInfo(reason="unsupported"),
                bios_version=mobo_info.get("bios_version") if "bios_version" in mobo_info else UnavailableInfo(reason="unsupported"),
            ),
            os=OsInfo(name=os_name, version=os_version, architecture=arch),
            memory=MemoryInfo(total_ram_bytes=total_ram),
            system=SystemInfo(hostname=hostname, username=username, python_version=py_ver, boot_time=boot_time),
            network=NetworkInfo(interfaces=network_interfaces),
        )

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
