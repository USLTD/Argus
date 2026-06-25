"""Fake driver for deterministic testing."""

from typing import Any, override

from backend.interfaces.caps import (
    BatteryMetric,
    CPUMetric,
    GPUMetric,
    MemoryMetric,
    MetricMetadata,
    MetricsCollection,
    NetworkMetric,
    ProcessMetric,
    SensorMetric,
    StorageMetric,
    SystemCapabilities,
)
from backend.interfaces.contexts import DriverContext
from backend.interfaces.enums import ConfidenceScore
from backend.interfaces.plugins import BaseDriver, PluginMeta
from backend.interfaces.sentinels import Unavailable


METADATA: PluginMeta = {
    "name": "Fake Test Driver",
    "author": "Test Suite",
    "version": "99.9",
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
    def tick_cpu(self, ctx: DriverContext) -> MetricsCollection[CPUMetric] | Unavailable:
        return MetricsCollection[CPUMetric](
            metadata=MetricMetadata(),
            metrics=[CPUMetric(usage_percent=42.5, core_id=None)],
        )

    @override
    def tick_memory(self, ctx: DriverContext) -> MetricsCollection[MemoryMetric] | Unavailable:
        return MetricsCollection[MemoryMetric](
            metadata=MetricMetadata(),
            metrics=[
                MemoryMetric(
                    total_bytes=8192000,
                    used_bytes=4096000,
                    available_bytes=4096000,
                    percent=50.0,
                )
            ],
        )

    @override
    def tick_processes(self, ctx: DriverContext) -> MetricsCollection[ProcessMetric] | Unavailable:
        return MetricsCollection[ProcessMetric](
            metadata=MetricMetadata(),
            metrics=[
                ProcessMetric(
                    pid=1, name="init", cpu_percent=5.0,
                    memory_rss=1024, status="running",
                ),
                ProcessMetric(
                    pid=2, name="test_proc", cpu_percent=30.0,
                    memory_rss=2048, status="sleeping",
                ),
            ],
        )

    @override
    def tick_gpu(self, ctx: DriverContext) -> MetricsCollection[GPUMetric] | Unavailable:
        return MetricsCollection[GPUMetric](
            metadata=MetricMetadata(),
            metrics=[
                GPUMetric(
                    name="FakeGPU", usage_percent=30.0,
                    memory_total=1073741824, memory_used=536870912,
                )
            ],
        )

    @override
    def tick_sensors(self, ctx: DriverContext) -> MetricsCollection[SensorMetric] | Unavailable:
        return MetricsCollection[SensorMetric](
            metadata=MetricMetadata(),
            metrics=[SensorMetric(name="cpu_package", value=65.0)],
        )

    @override
    def tick_battery(self, ctx: DriverContext) -> MetricsCollection[BatteryMetric] | Unavailable:
        return MetricsCollection[BatteryMetric](
            metadata=MetricMetadata(),
            metrics=[BatteryMetric(percent=85.0, power_plugged=True, seconds_left=None)],
        )

    @override
    def tick_disk(self, ctx: DriverContext) -> MetricsCollection[StorageMetric] | Unavailable:
        return Unavailable("unsupported", "Storage not available in test driver")

    @override
    def tick_network(self, ctx: DriverContext) -> MetricsCollection[NetworkMetric] | Unavailable:
        return Unavailable("unsupported", "Network not available in test driver")

    @override
    def manage_process(self, pid: int, action: str, **kwargs: Any) -> bool:
        return action == "kill" and pid > 0


DRIVER = FakeDriver
