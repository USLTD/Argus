from __future__ import annotations

from enum import IntEnum, StrEnum
from typing import Literal


class ConfidenceScore(IntEnum):
    INCOMPATIBLE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    FULL = 4


class CompatAction(StrEnum):
    LOAD = "load"
    SKIP = "skip"


class Permission(StrEnum):
    SCRIPT_READ_ONLY = "SCRIPT.READ_ONLY"
    SYSTEM_READ = "SYSTEM.READ"
    PROCESS_KILL = "PROCESS.KILL"
    DRIVER_READ = "DRIVER.READ"
    DRIVER_READ_CAPABILITIES = "DRIVER.READ_CAPABILITIES"
    DRIVER_READ_METADATA = "DRIVER.READ_METADATA"


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
]
"""Literal type for event names used in hook injection and dispatch."""
