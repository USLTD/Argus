"""Convert BackendEngine TickSnapshot to SystemMetrics for DB persistence."""

from __future__ import annotations

from backend.interfaces.caps import (
    BatteryMetric, CPUMetric, GPUMetric, MemoryMetric,
    MetricsCollection, NetworkMetric, ProcessMetric,
    SensorMetric, StorageMetric, SystemMetrics, UserMetric,
)
from backend.interfaces.sentinels import TickSnapshot, Unavailable


def snapshot_to_system_metrics(snapshot: TickSnapshot) -> SystemMetrics:
    """Convert a TickSnapshot to a SystemMetrics for DB storage.
    
    Unavailable fields become empty MetricsCollections.
    """
    cpu_val: MetricsCollection[CPUMetric] | None = (
        None if isinstance(snapshot.cpu, Unavailable) else snapshot.cpu
    )
    mem_val: MetricsCollection[MemoryMetric] | None = (
        None if isinstance(snapshot.memory, Unavailable) else snapshot.memory
    )
    procs_val: MetricsCollection[ProcessMetric] | None = (
        None if isinstance(snapshot.processes, Unavailable) else snapshot.processes
    )
    disk_val: MetricsCollection[StorageMetric] | None = (
        None if isinstance(snapshot.disk, Unavailable) else snapshot.disk
    )
    net_val: MetricsCollection[NetworkMetric] | None = (
        None if isinstance(snapshot.network, Unavailable) else snapshot.network
    )
    gpu_val: MetricsCollection[GPUMetric] | None = (
        None if isinstance(snapshot.gpu, Unavailable) else snapshot.gpu
    )
    sens_val: MetricsCollection[SensorMetric] | None = (
        None if isinstance(snapshot.sensors, Unavailable) else snapshot.sensors
    )
    bat_val: MetricsCollection[BatteryMetric] | None = (
        None if isinstance(snapshot.battery, Unavailable) else snapshot.battery
    )
    users_val: MetricsCollection[UserMetric] | None = (
        None if isinstance(snapshot.users, Unavailable) else snapshot.users
    )

    return SystemMetrics(
        cpu=cpu_val or MetricsCollection[CPUMetric](),
        ram=mem_val or MetricsCollection[MemoryMetric](),
        processes=procs_val or MetricsCollection[ProcessMetric](),
        storage=disk_val or MetricsCollection[StorageMetric](),
        network=net_val or MetricsCollection[NetworkMetric](),
        gpu=gpu_val or MetricsCollection[GPUMetric](),
        sensors=sens_val or MetricsCollection[SensorMetric](),
        battery=bat_val or MetricsCollection[BatteryMetric](),
        users=users_val or MetricsCollection[UserMetric](),
    )
