import time

from backend.interfaces.caps import (
    BatteryMetric,
    BatteryMetrics,
    CPUMetric,
    CPUMetrics,
    GPUMetric,
    GPUMetrics,
    MemoryMetric,
    MemoryMetrics,
    MetricMetadata,
    ProcessMetric,
    SensorMetric,
    SensorMetrics,
    SystemCapabilities,
    SystemMetrics,
)


class TestSystemCapabilities:
    def test_defaults(self) -> None:
        caps = SystemCapabilities()
        assert caps.has_process_list is False
        assert caps.has_gpu is False
        assert caps.has_storage is False
        assert caps.has_battery is False

    def test_extra_fields_allowed(self) -> None:
        caps = SystemCapabilities(has_gpu=True, custom_field="ignored")  # type: ignore[call-arg]
        assert caps.has_gpu is True
        assert caps.model_extra == {"custom_field": "ignored"}


def _cpu(cpu_percent: float = 50.0) -> CPUMetrics:
    """Helper: build a CPUMetrics with sensible defaults."""
    return CPUMetrics(
        metadata=MetricMetadata(collected_at=time.time()),
        metrics=[CPUMetric(usage_percent=cpu_percent)],
    )


def _ram() -> MemoryMetrics:
    """Helper: build a MemoryMetrics with sensible defaults."""
    return MemoryMetrics(
        metadata=MetricMetadata(collected_at=time.time()),
        metrics=[MemoryMetric(total_bytes=1000, used_bytes=500, available_bytes=500, percent=50.0)],
    )


class TestProcessMetric:
    def test_username_optional(self) -> None:
        p = ProcessMetric(
            pid=1, name="test", cpu_percent=10.0, memory_rss=0, status="running"
        )
        assert p.username is None

    def test_username_provided(self) -> None:
        p = ProcessMetric(
            pid=1,
            name="test",
            cpu_percent=10.0,
            memory_rss=0,
            status="running",
            username="root",
        )
        assert p.username == "root"


class TestGPUMetrics:
    def test_minimal(self) -> None:
        g = GPUMetrics(
            metadata=MetricMetadata(collected_at=time.time()),
            metrics=[
                GPUMetric(
                    name="TestGPU", usage_percent=50.0, memory_total=1000, memory_used=500
                )
            ],
        )
        assert g.metrics[0].usage_percent == 50.0


class TestSensorMetric:
    def test_default_unit(self) -> None:
        s = SensorMetric(name="cpu", value=70.0)
        assert s.unit == "celsius"

    def test_custom_unit(self) -> None:
        s = SensorMetric(name="fan", value=2500, unit="rpm")
        assert s.unit == "rpm"


class TestBatteryMetric:
    def test_minimal(self) -> None:
        b = BatteryMetric(percent=50.0)
        assert b.percent == 50.0
        assert b.power_plugged is None
        assert b.seconds_left is None

    def test_full(self) -> None:
        b = BatteryMetric(percent=100.0, power_plugged=True, seconds_left=3600.0)
        assert b.power_plugged is True
        assert b.seconds_left == 3600.0


class TestSystemMetrics:
    def test_minimal_metrics(self) -> None:
        m = SystemMetrics(cpu=_cpu(), ram=_ram())
        assert m.processes is None
        assert m.storage is None
        assert m.network is None
        assert m.sensors is None
        assert m.gpu is None
        assert m.battery is None

    def test_extra_fields_allowed(self) -> None:
        m = SystemMetrics(cpu=_cpu(), ram=_ram(), extra_metric="passthrough")  # type: ignore[call-arg]
        assert m.model_extra == {"extra_metric": "passthrough"}

    def test_gpu_list(self) -> None:
        gpus = GPUMetrics(
            metadata=MetricMetadata(collected_at=time.time()),
            metrics=[
                GPUMetric(
                    name="Test", usage_percent=30.0, memory_total=1000, memory_used=200
                )
            ],
        )
        m = SystemMetrics(cpu=_cpu(), ram=_ram(), gpu=gpus)
        assert m.gpu is not None
        assert len(m.gpu.metrics) == 1

    def test_battery(self) -> None:
        b = BatteryMetrics(
            metadata=MetricMetadata(collected_at=time.time()),
            metrics=[BatteryMetric(percent=75.0)],
        )
        m = SystemMetrics(cpu=_cpu(), ram=_ram(), battery=b)
        assert m.battery is not None
        assert m.battery.metrics[0].percent == 75.0
