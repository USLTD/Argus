from __future__ import annotations

from enum import IntEnum, StrEnum
from typing import Literal


class ConfidenceScore(IntEnum):
    INCOMPATIBLE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    FULL = 4


class ScriptExecutionMode(IntEnum):
    NONBLOCKING = 1
    BLOCKING = 2
    MIXED = 3


class CompatAction(StrEnum):
    LOAD = "load"
    SKIP = "skip"


class Permission(StrEnum):
    # Script system (special, outside subsystem hierarchy)
    SCRIPT_READ = "SCRIPT.READ"

    # System
    SYSTEM_READ = "SYSTEM.READ"
    SYSTEM_WRITE = "SYSTEM.WRITE"
    SYSTEM_EXECUTE = "SYSTEM.EXECUTE"

    # CPU
    CPU_READ = "CPU.READ"
    CPU_WRITE = "CPU.WRITE"
    CPU_EXECUTE = "CPU.EXECUTE"
    CPU_CORES_READ_INFO = "CPU.CORES.READ.INFO"
    CPU_CORES_READ_METRICS = "CPU.CORES.READ.METRICS"

    # Memory
    MEMORY_READ = "MEMORY.READ"
    MEMORY_WRITE = "MEMORY.WRITE"
    MEMORY_EXECUTE = "MEMORY.EXECUTE"

    # Disk
    DISK_READ = "DISK.READ"
    DISK_WRITE = "DISK.WRITE"
    DISK_EXECUTE = "DISK.EXECUTE"
    DISK_PARTITIONS_READ_INFO = "DISK.PARTITIONS.READ.INFO"
    DISK_PARTITIONS_READ_METRICS = "DISK.PARTITIONS.READ.METRICS"

    # Network
    NETWORK_READ = "NETWORK.READ"
    NETWORK_WRITE = "NETWORK.WRITE"
    NETWORK_EXECUTE = "NETWORK.EXECUTE"
    NETWORK_INTERFACES_READ_INFO = "NETWORK.INTERFACES.READ.INFO"
    NETWORK_INTERFACES_READ_METRICS = "NETWORK.INTERFACES.READ.METRICS"

    # Processes
    PROCESSES_READ = "PROCESSES.READ"
    PROCESSES_WRITE = "PROCESSES.WRITE"
    PROCESSES_EXECUTE = "PROCESSES.EXECUTE"
    PROCESSES_LIST_READ_INFO = "PROCESSES.LIST.READ.INFO"
    PROCESSES_LIST_READ_METRICS = "PROCESSES.LIST.READ.METRICS"

    # GPU
    GPU_READ = "GPU.READ"
    GPU_WRITE = "GPU.WRITE"
    GPU_EXECUTE = "GPU.EXECUTE"

    # Sensors
    SENSORS_READ = "SENSORS.READ"
    SENSORS_WRITE = "SENSORS.WRITE"
    SENSORS_EXECUTE = "SENSORS.EXECUTE"

    # Battery
    BATTERY_READ = "BATTERY.READ"
    BATTERY_WRITE = "BATTERY.WRITE"
    BATTERY_EXECUTE = "BATTERY.EXECUTE"
    BATTERY_INFO_READ = "BATTERY.INFO.READ"
    BATTERY_METRICS_READ = "BATTERY.METRICS.READ"


EventName: Literal[
    "on_load",
    "on_unload",
    "on_tick",
    "cpu.on_tick",
    "memory.on_tick",
    "disk.on_read",
    "disk.on_write",
    "net.on_rx",
    "net.on_tx",
    "process.on_spawn",
    "process.on_exit",
    "gpu.on_tick",
    "battery.on_tick",
    "sensor.on_tick",
    "users.on_tick",
]
"""Literal type for event names used in hook injection and dispatch."""
