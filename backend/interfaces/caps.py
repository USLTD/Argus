from __future__ import annotations

from typing import Generic, TypeAlias, TypeVar

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


class BatteryMetric(BaseModel):
    percent: float = 0.0
    power_plugged: bool | None = None
    seconds_left: float | None = None


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
# Static info
# ---------------------------------------------------------------------------


class StaticSystemInfo(BaseModel):
    os_name: str
    os_version: str
    hostname: str
    username: str
    cpu_brand: str
    cpu_physical_cores: int
    cpu_logical_cores: int
    cpu_frequency_mhz: float | None = None
    gpu_name: str | None = None
    gpu_driver: str | None = None
    gpu_vram_bytes: int | None = None
    motherboard_manufacturer: str | None = None
    motherboard_model: str | None = None
    bios_version: str | None = None
    total_ram_bytes: int
    architecture: str
    python_version: str
    boot_time: str


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
