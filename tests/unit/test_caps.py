import time

from backend.interfaces.caps import (
    BatteryMetric,
    BatteryMetrics,
    CPUMetric,
    CPUMetrics,
    CpuInfo,
    GPUMetric,
    GPUMetrics,
    GpuInfo,
    MemoryInfo,
    MemoryMetric,
    MemoryMetrics,
    MetricMetadata,
    MotherboardInfo,
    OsInfo,
    ProcessMetric,
    SensorMetric,
    SensorMetrics,
    StaticSystemInfo,
    SystemCapabilities,
    SystemInfo,
    SystemMetrics,
    UnavailableInfo,
    UserMetric,
    UserMetrics,
    dump_static_info,
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

    def test_default_category(self) -> None:
        s = SensorMetric(name="cpu", value=70.0)
        assert s.category == "unknown"

    def test_custom_category(self) -> None:
        s = SensorMetric(name="cpu", value=70.0, category="temperature")
        assert s.category == "temperature"


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


class TestUserMetric:
    def test_default(self) -> None:
        u = UserMetric()
        assert u.name == ""
        assert u.terminal is None
        assert u.host is None
        assert u.started == 0.0

    def test_all_fields(self) -> None:
        u = UserMetric(name="alice", terminal="/dev/pts/0", host="laptop", started=1000.0)
        assert u.name == "alice"
        assert u.terminal == "/dev/pts/0"
        assert u.host == "laptop"
        assert u.started == 1000.0


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

    def test_users(self) -> None:
        users = UserMetrics(
            metadata=MetricMetadata(collected_at=time.time()),
            metrics=[UserMetric(name="bob", started=100.0)],
        )
        m = SystemMetrics(cpu=_cpu(), ram=_ram(), users=users)
        assert m.users is not None
        assert len(m.users.metrics) == 1
        assert m.users.metrics[0].name == "bob"


class TestCpuInfo:
    def test_happy_path(self) -> None:
        c = CpuInfo(name="Intel i7", physical_cores=4, logical_cores=8, frequency_mhz=3500.0)
        d = c.model_dump()
        assert d["name"] == "Intel i7"
        assert d["physical_cores"] == 4
        assert d["frequency_mhz"] == 3500.0

    def test_with_unavailable(self) -> None:
        c = CpuInfo(
            name="Intel i7",
            physical_cores=4,
            logical_cores=8,
            frequency_mhz=UnavailableInfo(reason="unsupported"),
        )
        d = c.model_dump()
        assert d["name"] == "Intel i7"
        assert d["frequency_mhz"] == {"unavailable": True, "reason": "unsupported", "detail": ""}

    def test_defaults(self) -> None:
        c = CpuInfo()
        d = c.model_dump()
        assert d["name"] == {"unavailable": True, "reason": "unsupported", "detail": ""}
        assert d["physical_cores"] == {"unavailable": True, "reason": "unsupported", "detail": ""}

    def test_frequency_none(self) -> None:
        c = CpuInfo(name="test", physical_cores=2, logical_cores=4, frequency_mhz=None)
        d = c.model_dump()
        assert d["frequency_mhz"] is None


class TestGpuInfo:
    def test_happy_path(self) -> None:
        g = GpuInfo(name="RTX 4090", driver="565.90", vram_bytes=24_576_000_000)
        d = g.model_dump()
        assert d["name"] == "RTX 4090"
        assert d["driver"] == "565.90"

    def test_unavailable(self) -> None:
        g = GpuInfo(
            name=UnavailableInfo(reason="unsupported"),
            driver=UnavailableInfo(reason="unsupported"),
            vram_bytes=UnavailableInfo(reason="unsupported"),
        )
        d = g.model_dump()
        assert d["name"]["unavailable"] is True


class TestStaticSystemInfo:
    def test_full_construction(self) -> None:
        info = StaticSystemInfo(
            cpu=CpuInfo(name="Test CPU", physical_cores=4, logical_cores=8, frequency_mhz=3000.0),
            gpu=GpuInfo(name="Test GPU", driver="v1", vram_bytes=8000),
            motherboard=MotherboardInfo(manufacturer="ASUS", model="Z790", bios_version="v2.1"),
            os=OsInfo(name="Windows", version="10", architecture="x64"),
            memory=MemoryInfo(total_ram_bytes=16_000_000_000),
            system=SystemInfo(hostname="pc", username="user", python_version="3.12", boot_time="2024-01-01"),
        )
        d = info.model_dump()
        assert d["cpu"]["name"] == "Test CPU"
        assert d["gpu"]["name"] == "Test GPU"
        assert d["motherboard"]["manufacturer"] == "ASUS"
        assert d["os"]["name"] == "Windows"
        assert d["memory"]["total_ram_bytes"] == 16_000_000_000
        assert d["system"]["hostname"] == "pc"

    def test_unavailable_fields(self) -> None:
        info = StaticSystemInfo(
            cpu=CpuInfo(name="CPU", physical_cores=4, logical_cores=8, frequency_mhz=UnavailableInfo(reason="error", detail="failed to read")),
            gpu=GpuInfo(
                name=UnavailableInfo(reason="unsupported"),
                driver=UnavailableInfo(reason="unsupported"),
                vram_bytes=UnavailableInfo(reason="unsupported"),
            ),
            motherboard=MotherboardInfo(manufacturer="ASUS", model="Z790", bios_version=None),
            os=OsInfo(name="Linux", version="Ubuntu", architecture="x64"),
            memory=MemoryInfo(total_ram_bytes=8000),
            system=SystemInfo(hostname="srv", username="root", python_version="3.11", boot_time="2024-06-01"),
        )
        d = info.model_dump()
        assert d["cpu"]["frequency_mhz"] == {"unavailable": True, "reason": "error", "detail": "failed to read"}
        assert d["gpu"]["name"] == {"unavailable": True, "reason": "unsupported", "detail": ""}

    def test_dump_static_info(self) -> None:
        info = StaticSystemInfo(
            cpu=CpuInfo(name="CPU", physical_cores=4, logical_cores=8, frequency_mhz=3000.0),
            gpu=GpuInfo(
                name=UnavailableInfo(reason="unsupported"),
                driver=UnavailableInfo(reason="unsupported"),
                vram_bytes=UnavailableInfo(reason="unsupported"),
            ),
            motherboard=MotherboardInfo(manufacturer="MFR", model="X", bios_version="1.0"),
            os=OsInfo(name="OS", version="1", architecture="x86"),
            memory=MemoryInfo(total_ram_bytes=4096),
            system=SystemInfo(hostname="h", username="u", python_version="3.9", boot_time="now"),
        )
        d = dump_static_info(info)
        assert d["cpu"]["name"] == "CPU"
        assert d["gpu"]["name"] == {"unavailable": True, "reason": "unsupported", "detail": ""}
        # Also verify the model_dump roundtrip doesn't raise
        _ = info.model_dump(mode="json")
