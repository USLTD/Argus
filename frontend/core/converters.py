"""Pure conversion functions: MetricsCollection[T] → flat dicts.

These functions have NO GUI dependencies. They are used by both
SyncBridge (Textual) and EngineBridge (PyQt6).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.interfaces.caps import (
        BatteryMetric, CPUMetric, MemoryMetric,
        MetricsCollection, NetworkMetric, ProcessMetric,
        SensorMetric, StorageMetric,
    )
    from backend.interfaces.sentinels import Unavailable as UnavailableType


def cpu_collection_to_dict(
    cpu: "MetricsCollection[CPUMetric] | UnavailableType",
    static_cores: int = 0,
    static_threads: int = 0,
) -> dict:
    """Convert CPU MetricsCollection + static info → flat dict.
    
    If Unavailable, returns zero-filled dict.
    """
    from backend.interfaces.sentinels import Unavailable
    if isinstance(cpu, Unavailable):
        return {
            "cpu_percent": 0.0,
            "per_core": [],
            "frequency": None,
            "physical_cores": static_cores,
            "logical_cores": static_threads,
        }
    metrics = cpu.metrics
    aggregate = next((m for m in metrics if m.core_id is None), None)
    per_core = [m.usage_percent for m in metrics if m.core_id is not None]
    return {
        "cpu_percent": aggregate.usage_percent if aggregate else 0.0,
        "per_core": per_core,
        "frequency": aggregate.frequency_mhz if aggregate else None,
        "physical_cores": static_cores,
        "logical_cores": static_threads,
    }


def memory_collection_to_dict(
    memory: "MetricsCollection[MemoryMetric] | UnavailableType",
) -> dict:
    """Convert Memory MetricsCollection → flat dict."""
    from backend.interfaces.sentinels import Unavailable
    if isinstance(memory, Unavailable):
        return {"total": 0, "used": 0, "available": 0, "free": 0, "cached": 0, "percent": 0.0}
    m = memory.metrics[0] if memory.metrics else None
    if m is None:
        return {"total": 0, "used": 0, "available": 0, "free": 0, "cached": 0, "percent": 0.0}
    return {
        "total": m.total_bytes,
        "used": m.used_bytes,
        "available": m.available_bytes,
        "free": m.available_bytes,
        "cached": 0,
        "percent": m.percent,
    }


def disk_collection_to_dict(
    disk: "MetricsCollection[StorageMetric] | UnavailableType",
    mount_point: str = "/",
) -> dict:
    """Find the disk entry for *mount_point*, return as flat dict."""
    from backend.interfaces.sentinels import Unavailable
    if isinstance(disk, Unavailable):
        return {"total": 0, "used": 0, "free": 0, "percent": 0.0}
    for d in disk.metrics:
        if d.mount_point == mount_point:
            return {
                "total": d.total_bytes,
                "used": d.used_bytes,
                "free": d.free_bytes,
                "percent": d.percent,
            }
    return {"total": 0, "used": 0, "free": 0, "percent": 0.0}


def network_collection_to_dict(
    network: "MetricsCollection[NetworkMetric] | UnavailableType",
) -> dict:
    """Aggregate all interfaces into bytes_sent / bytes_recv."""
    from backend.interfaces.sentinels import Unavailable
    if isinstance(network, Unavailable):
        return {"bytes_sent": 0, "bytes_recv": 0}
    total_sent = sum(m.bytes_sent for m in network.metrics)
    total_recv = sum(m.bytes_recv for m in network.metrics)
    return {"bytes_sent": total_sent, "bytes_recv": total_recv}


def process_collection_to_dict(
    processes: "MetricsCollection[ProcessMetric] | UnavailableType",
) -> list[dict]:
    """Convert processes collection → list of flat dicts."""
    from backend.interfaces.sentinels import Unavailable
    if isinstance(processes, Unavailable):
        return []
    result = []
    for p in processes.metrics:
        result.append({
            "pid": p.pid,
            "name": p.name,
            "cpu_percent": p.cpu_percent,
            "memory_info": p.memory_rss,
            "status": p.status,
            "num_threads": 0,
            "username": p.username,
            "ppid": None,
            "create_time": None,
            "exe": None,
        })
    return result


def sensor_collection_to_dict(
    sensors: "MetricsCollection[SensorMetric] | UnavailableType",
) -> dict:
    """Group sensors by name → list of values."""
    from backend.interfaces.sentinels import Unavailable
    if isinstance(sensors, Unavailable):
        return {"temperatures": {}}
    temps: dict[str, list[float]] = {}
    for s in sensors.metrics:
        temps.setdefault(s.name, []).append(s.value)
    return {"temperatures": temps}


def battery_collection_to_dict(
    battery: "MetricsCollection[BatteryMetric] | UnavailableType",
) -> dict:
    """Convert battery collection → flat dict."""
    from backend.interfaces.sentinels import Unavailable
    if isinstance(battery, Unavailable):
        return {"percent": 0.0, "power_plugged": None, "seconds_left": None}
    b = battery.metrics[0] if battery.metrics else None
    if b is None:
        return {"percent": 0.0, "power_plugged": None, "seconds_left": None}
    return {
        "percent": b.percent,
        "power_plugged": b.power_plugged,
        "seconds_left": b.seconds_left,
    }
