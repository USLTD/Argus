"""Fake driver for deterministic testing."""

from typing import Any, override

from backend.interfaces.caps import (
    BatteryMetrics,
    CPUMetrics,
    GPUMetrics,
    ProcessInfo,
    RAMMetrics,
    SensorReading,
    SystemCapabilities,
    SystemMetrics,
)
from backend.interfaces.enums import ConfidenceScore, Permission
from backend.interfaces.plugins import BaseDriver, PluginMeta


METADATA: PluginMeta = {
    "name": "Fake Test Driver",
    "author": "Test Suite",
    "version": "99.9",
    "permissions": [Permission.SYSTEM_READ, Permission.PROCESS_KILL],
    "compatible": lambda ctx: ConfidenceScore.FULL,
}


class FakeDriver(BaseDriver):
    @override
    def get_capabilities(self) -> SystemCapabilities:
        return SystemCapabilities(
            has_process_list=True,
            has_gpu=True,
            has_storage=False,
            has_network=False,
            has_sensors=True,
            has_battery=True,
        )

    @override
    def fetch_metrics(self) -> SystemMetrics:
        return SystemMetrics(
            cpu=CPUMetrics(physical_cores=2, logical_cores=4, usage_percent=42.5),
            ram=RAMMetrics(
                total_bytes=8192000,
                used_bytes=4096000,
                available_bytes=4096000,
                percent=50.0,
            ),
            processes=[
                ProcessInfo(
                    pid=1,
                    name="init",
                    cpu_percent=5.0,
                    memory_rss=1024,
                    status="running",
                ),
                ProcessInfo(
                    pid=2,
                    name="test_proc",
                    cpu_percent=30.0,
                    memory_rss=2048,
                    status="sleeping",
                ),
            ],
            gpu=[
                GPUMetrics(
                    name="FakeGPU",
                    usage_percent=30.0,
                    memory_total=1073741824,
                    memory_used=536870912,
                )
            ],
            sensors=[SensorReading(name="cpu_package", value=65.0)],
            battery=BatteryMetrics(percent=85.0, power_plugged=True, seconds_left=None),
        )

    @override
    def manage_process(self, pid: int, action: str, **kwargs: Any) -> bool:
        return action == "kill" and pid > 0


DRIVER = FakeDriver
