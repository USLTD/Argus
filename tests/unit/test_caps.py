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


class TestSystemCapabilities:
    def test_defaults(self) -> None:
        caps = SystemCapabilities()
        assert caps.has_process_list is False
        assert caps.has_gpu is False
        assert caps.has_storage is False
        assert caps.has_battery is False

    def test_extra_fields_allowed(self) -> None:
        caps = SystemCapabilities(has_gpu=True, custom_field="ignored")
        assert caps.has_gpu is True
        assert caps.model_extra == {"custom_field": "ignored"}


class TestProcessInfo:
    def test_username_optional(self) -> None:
        p = ProcessInfo(
            pid=1, name="test", cpu_percent=10.0, memory_rss=0, status="running"
        )
        assert p.username is None

    def test_username_provided(self) -> None:
        p = ProcessInfo(
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
            name="TestGPU", usage_percent=50.0, memory_total=1000, memory_used=500
        )
        assert g.usage_percent == 50.0


class TestSensorReading:
    def test_default_unit(self) -> None:
        s = SensorReading(name="cpu", value=70.0)
        assert s.unit == "celsius"

    def test_custom_unit(self) -> None:
        s = SensorReading(name="fan", value=2500, unit="rpm")
        assert s.unit == "rpm"


class TestBatteryMetrics:
    def test_minimal(self) -> None:
        b = BatteryMetrics(percent=50.0)
        assert b.percent == 50.0
        assert b.power_plugged is None
        assert b.seconds_left is None

    def test_full(self) -> None:
        b = BatteryMetrics(percent=100.0, power_plugged=True, seconds_left=3600.0)
        assert b.power_plugged is True
        assert b.seconds_left == 3600.0


class TestSystemMetrics:
    def test_minimal_metrics(self) -> None:
        cpu = CPUMetrics(physical_cores=2, logical_cores=4, usage_percent=50.0)
        ram = RAMMetrics(
            total_bytes=1000, used_bytes=500, available_bytes=500, percent=50.0
        )
        m = SystemMetrics(cpu=cpu, ram=ram)
        assert m.processes is None
        assert m.storage == []
        assert m.network is None
        assert m.sensors is None
        assert m.gpu is None
        assert m.battery is None

    def test_extra_fields_allowed(self) -> None:
        cpu = CPUMetrics(physical_cores=2, logical_cores=4, usage_percent=50.0)
        ram = RAMMetrics(
            total_bytes=1000, used_bytes=500, available_bytes=500, percent=50.0
        )
        m = SystemMetrics(cpu=cpu, ram=ram, extra_metric="passthrough")
        assert m.model_extra == {"extra_metric": "passthrough"}

    def test_gpu_list(self) -> None:
        cpu = CPUMetrics(physical_cores=2, logical_cores=4, usage_percent=50.0)
        ram = RAMMetrics(
            total_bytes=1000, used_bytes=500, available_bytes=500, percent=50.0
        )
        gpu = [
            GPUMetrics(
                name="Test", usage_percent=30.0, memory_total=1000, memory_used=200
            )
        ]
        m = SystemMetrics(cpu=cpu, ram=ram, gpu=gpu)
        assert m.gpu is not None
        assert len(m.gpu) == 1

    def test_battery(self) -> None:
        cpu = CPUMetrics(physical_cores=2, logical_cores=4, usage_percent=50.0)
        ram = RAMMetrics(
            total_bytes=1000, used_bytes=500, available_bytes=500, percent=50.0
        )
        b = BatteryMetrics(percent=75.0)
        m = SystemMetrics(cpu=cpu, ram=ram, battery=b)
        assert m.battery is not None
        assert m.battery.percent == 75.0
