from pydantic import BaseModel, ConfigDict


class SystemCapabilities(BaseModel):
    model_config = ConfigDict(extra="allow")

    has_process_list: bool = False
    has_gpu: bool = False
    has_storage: bool = False
    has_network: bool = False
    has_sensors: bool = False
    has_battery: bool = False


class CPUMetrics(BaseModel):
    physical_cores: int
    logical_cores: int
    usage_percent: float


class RAMMetrics(BaseModel):
    total_bytes: int
    used_bytes: int
    available_bytes: int
    percent: float


class ProcessInfo(BaseModel):
    pid: int
    name: str
    cpu_percent: float
    memory_rss: int
    status: str
    username: str | None = None


class StorageMetrics(BaseModel):
    mount_point: str
    total_bytes: int
    used_bytes: int
    free_bytes: int
    percent: float


class GPUMetrics(BaseModel):
    name: str
    usage_percent: float
    memory_total: int
    memory_used: int


class NetworkMetrics(BaseModel):
    bytes_sent: int
    bytes_recv: int
    packets_sent: int
    packets_recv: int


class SensorReading(BaseModel):
    name: str
    value: float
    unit: str = "celsius"


class BatteryMetrics(BaseModel):
    percent: float
    power_plugged: bool | None = None
    seconds_left: float | None = None


class SystemMetrics(BaseModel):
    model_config = ConfigDict(extra="allow")

    cpu: CPUMetrics
    ram: RAMMetrics
    processes: list[ProcessInfo] | None = None
    storage: list[StorageMetrics] = []
    gpu: list[GPUMetrics] | None = None
    network: list[NetworkMetrics] | None = None
    sensors: list[SensorReading] | None = None
    battery: BatteryMetrics | None = None
