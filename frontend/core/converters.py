"""Pure conversion functions: MetricsCollection[T] → flat dicts.

Re-exports from backend.bridges.converters — the canonical source.
"""

from backend.bridges.converters import (
    battery_collection_to_dict,
    cpu_collection_to_dict,
    disk_collection_to_dict,
    memory_collection_to_dict,
    network_collection_to_dict,
    process_collection_to_dict,
    sensor_collection_to_dict,
)

__all__ = [
    "battery_collection_to_dict",
    "cpu_collection_to_dict",
    "disk_collection_to_dict",
    "memory_collection_to_dict",
    "network_collection_to_dict",
    "process_collection_to_dict",
    "sensor_collection_to_dict",
]
