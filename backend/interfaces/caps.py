from __future__ import annotations

from typing import Any, Generic, TypeAlias, TypeVar, Union

from pydantic import BaseModel, ConfigDict


T = TypeVar("T", bound=BaseModel)


class MetricMetadata(BaseModel):
    collected_at: float = 0.0
    source: str = "driver"
    hostname: str = ""


class MetricsCollection(BaseModel, Generic[T]):
    metadata: MetricMetadata = MetricMetadata()
    metrics: list[T] = []


class SystemCapabilities(BaseModel):
    model_config = ConfigDict(extra="allow")

    has_process_list: bool = False
    has_gpu: bool = False
    has_storage: bool = False
    has_network: bool = False
    has_sensors: bool = False
    has_battery: bool = False

    cpu: CpuCapabilities | None = None
    gpu: GpuCapabilities | None = None
    process: ProcessCapabilities | None = None
    storage: StorageCapabilities | None = None
    network: NetworkCapabilities | None = None
    sensors: SensorCapabilities | None = None
    battery: BatteryCapabilities | None = None
    driver: DriverInfo | None = None


class CPUMetric(BaseModel):
    core_id: int | None = None
    usage_percent: float = 0.0
    frequency_mhz: float | None = None


class MemoryMetric(BaseModel):
    total_bytes: int = 0
    used_bytes: int = 0
    available_bytes: int = 0
    percent: float = 0.0


class ProcessMetric(BaseModel):
    pid: int = 0
    name: str = ""
    cpu_percent: float = 0.0
    memory_rss: int = 0
    status: str = ""
    username: str | None = None


class StorageMetric(BaseModel):
    mount_point: str = ""
    total_bytes: int = 0
    used_bytes: int = 0
    free_bytes: int = 0
    percent: float = 0.0


class GPUMetric(BaseModel):
    name: str = ""
    usage_percent: float = 0.0
    memory_total: int = 0
    memory_used: int = 0


class NetworkMetric(BaseModel):
    bytes_sent: int = 0
    bytes_recv: int = 0
    packets_sent: int = 0
    packets_recv: int = 0


class SensorMetric(BaseModel):
    name: str = ""
    value: float = 0.0
    unit: str = "celsius"
    category: str = "unknown"


class BatteryMetric(BaseModel):
    percent: float = 0.0
    power_plugged: bool | None = None
    seconds_left: float | None = None


class UserMetric(BaseModel):
    name: str = ""
    terminal: str | None = None
    host: str | None = None
    started: float = 0.0


# ---------------------------------------------------------------------------
# Type aliases for collections (backwards-compatible plural names)
# ---------------------------------------------------------------------------

CPUMetrics: TypeAlias = MetricsCollection[CPUMetric]
MemoryMetrics: TypeAlias = MetricsCollection[MemoryMetric]
ProcessMetrics: TypeAlias = MetricsCollection[ProcessMetric]
StorageMetrics: TypeAlias = MetricsCollection[StorageMetric]
NetworkMetrics: TypeAlias = MetricsCollection[NetworkMetric]
GPUMetrics: TypeAlias = MetricsCollection[GPUMetric]
SensorMetrics: TypeAlias = MetricsCollection[SensorMetric]
BatteryMetrics: TypeAlias = MetricsCollection[BatteryMetric]
UserMetrics: TypeAlias = MetricsCollection[UserMetric]

# ---------------------------------------------------------------------------
# Capability sub-models (used by get_capabilities())
# ---------------------------------------------------------------------------


class CpuCapabilities(BaseModel):
    present: bool = False
    frequency: bool = False
    core_count: bool = False


class GpuCapabilities(BaseModel):
    present: bool = False
    detail: bool = False


class ProcessCapabilities(BaseModel):
    list: bool = False
    detail: bool = False


class StorageCapabilities(BaseModel):
    present: bool = False
    disk_io: bool = False


class NetworkCapabilities(BaseModel):
    present: bool = False
    bandwidth: bool = False


class SensorCapabilities(BaseModel):
    present: bool = False


class BatteryCapabilities(BaseModel):
    present: bool = False


class DriverInfo(BaseModel):
    name: str = ""
    version: str = ""
    platform: str = ""


# ---------------------------------------------------------------------------
# Static info — sentinel / type alias
# ---------------------------------------------------------------------------


class UnavailableInfo(BaseModel):
    """Pydantic-compatible sentinel for unavailable static info.

    Mirror of the Unavailable frozen dataclass in sentinels.py, but as a BaseModel
    so model_dump() works natively through bridges.

    model_dump() produces: {"unavailable": True, "reason": "...", "detail": "..."}
    """

    unavailable: bool = True
    reason: str
    detail: str = ""


V = TypeVar("V")
StaticField: TypeAlias = V | UnavailableInfo


# ---------------------------------------------------------------------------
# Static info — sub-models
# ---------------------------------------------------------------------------


class CpuInfo(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: StaticField[str] = UnavailableInfo(reason="unsupported")
    physical_cores: StaticField[int] = UnavailableInfo(reason="unsupported")
    logical_cores: StaticField[int] = UnavailableInfo(reason="unsupported")
    frequency_mhz: StaticField[float | None] = UnavailableInfo(reason="unsupported")


class GpuInfo(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: StaticField[str | None] = UnavailableInfo(reason="unsupported")
    driver: StaticField[str | None] = UnavailableInfo(reason="unsupported")
    vram_bytes: StaticField[int | None] = UnavailableInfo(reason="unsupported")


class MotherboardInfo(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    manufacturer: StaticField[str | None] = UnavailableInfo(reason="unsupported")
    model: StaticField[str | None] = UnavailableInfo(reason="unsupported")
    bios_version: StaticField[str | None] = UnavailableInfo(reason="unsupported")


class OsInfo(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: StaticField[str] = UnavailableInfo(reason="unsupported")
    version: StaticField[str] = UnavailableInfo(reason="unsupported")
    architecture: StaticField[str] = UnavailableInfo(reason="unsupported")


class MemoryInfo(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    total_ram_bytes: StaticField[int] = UnavailableInfo(reason="unsupported")


class SystemInfo(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    hostname: StaticField[str] = UnavailableInfo(reason="unsupported")
    username: StaticField[str] = UnavailableInfo(reason="unsupported")
    python_version: StaticField[str] = UnavailableInfo(reason="unsupported")
    boot_time: StaticField[str] = UnavailableInfo(reason="unsupported")


# ---------------------------------------------------------------------------
# Static info — aggregate model
# ---------------------------------------------------------------------------


class NetworkInterfaceInfo(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: StaticField[str] = UnavailableInfo(reason="unsupported")
    family: StaticField[str] = UnavailableInfo(reason="unsupported")
    address: StaticField[str] = UnavailableInfo(reason="unsupported")
    netmask: StaticField[str | None] = None
    broadcast: StaticField[str | None] = None


class NetworkInfo(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    interfaces: list[NetworkInterfaceInfo] = []


class StaticSystemInfo(BaseModel):
    cpu: CpuInfo
    gpu: GpuInfo
    motherboard: MotherboardInfo
    os: OsInfo
    memory: MemoryInfo
    system: SystemInfo
    network: NetworkInfo = NetworkInfo()


def dump_static_info(info: StaticSystemInfo) -> dict:
    """Serialize StaticSystemInfo to nested dicts with UnavailableInfo converted."""
    raw = info.model_dump(mode="python")
    return _convert_unavailable(raw)


def _convert_unavailable(val: object) -> Any:
    """Recursively convert UnavailableInfo instances to dict."""
    if isinstance(val, UnavailableInfo):
        return val.model_dump()
    if isinstance(val, dict):
        return {k: _convert_unavailable(v) for k, v in val.items()}
    if isinstance(val, (list, tuple)):
        return [_convert_unavailable(v) for v in val]
    return val


class SystemMetrics(BaseModel):
    model_config = ConfigDict(extra="allow")

    cpu: MetricsCollection[CPUMetric] | None = None
    ram: MetricsCollection[MemoryMetric] | None = None
    processes: MetricsCollection[ProcessMetric] | None = None
    storage: MetricsCollection[StorageMetric] | None = None
    gpu: MetricsCollection[GPUMetric] | None = None
    network: MetricsCollection[NetworkMetric] | None = None
    sensors: MetricsCollection[SensorMetric] | None = None
    battery: MetricsCollection[BatteryMetric] | None = None
    users: MetricsCollection[UserMetric] | None = None
