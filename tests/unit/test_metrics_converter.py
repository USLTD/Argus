"""Tests for ``frontend/core/metrics_converter.py`` and the engine's
``on_tick_callback`` mechanism.
"""

from __future__ import annotations

from backend.core.engine import BackendEngine
from backend.interfaces.caps import (
    BatteryMetric,
    CPUMetric,
    GPUMetric,
    MemoryMetric,
    MetricsCollection,
    NetworkMetric,
    ProcessMetric,
    SensorMetric,
    StorageMetric,
    SystemMetrics,
    UserMetric,
)
from backend.interfaces.sentinels import TickSnapshot, Unavailable
from frontend.core.metrics_converter import snapshot_to_system_metrics
from tests.fake_driver import FakeDriver


# ===================================================================
# Helper
# ===================================================================


def _engine_with_callback() -> tuple[BackendEngine, list[TickSnapshot]]:
    """Create a BackendEngine with a recording on_tick_callback.

    Returns (engine, call_record) where call_record accumulates every
    TickSnapshot the callback receives.
    """
    calls: list[TickSnapshot] = []

    def record(snap: TickSnapshot) -> None:
        calls.append(snap)

    eng = BackendEngine(on_tick_callback=record)
    eng.loader.active_driver = FakeDriver()
    eng.loader.active_scripts = []
    return eng, calls


# ===================================================================
# Tests: snapshot_to_system_metrics
# ===================================================================


class TestSnapshotToSystemMetrics:
    """Exercise ``snapshot_to_system_metrics()``."""

    # -- Test 1 --------------------------------------------------------

    def test_converts_snapshot_correctly(self) -> None:
        """TickSnapshot with known MetricsCollection values
        produces a SystemMetrics with correctly populated fields.
        """
        cpu_metric = CPUMetric(core_id=None, usage_percent=42.5, frequency_mhz=3500.0)
        mem_metric = MemoryMetric(
            total_bytes=8_192_000,
            used_bytes=4_096_000,
            available_bytes=4_096_000,
            percent=50.0,
        )
        proc_a = ProcessMetric(
            pid=1,
            name="init",
            cpu_percent=5.0,
            memory_rss=1024,
            status="running",
        )
        proc_b = ProcessMetric(
            pid=2,
            name="test_proc",
            cpu_percent=30.0,
            memory_rss=2048,
            status="sleeping",
        )
        disk_metric = StorageMetric(
            mount_point="/",
            total_bytes=500_000_000_000,
            used_bytes=250_000_000_000,
            free_bytes=250_000_000_000,
            percent=50.0,
        )
        net_metric = NetworkMetric(
            bytes_sent=1000,
            bytes_recv=2000,
            packets_sent=10,
            packets_recv=20,
        )
        gpu_metric = GPUMetric(
            name="FakeGPU",
            usage_percent=30.0,
            memory_total=1_073_741_824,
            memory_used=536_870_912,
        )
        sensor_metric = SensorMetric(
            name="cpu_package",
            value=65.0,
            unit="celsius",
            category="temperature",
        )
        bat_metric = BatteryMetric(
            percent=85.0,
            power_plugged=True,
            seconds_left=None,
        )
        user_metric = UserMetric(
            name="testuser",
            terminal="tty1",
            host=None,
            started=1000.0,
        )

        snap = TickSnapshot(
            cpu=MetricsCollection[CPUMetric](metrics=[cpu_metric]),
            memory=MetricsCollection[MemoryMetric](metrics=[mem_metric]),
            processes=MetricsCollection[ProcessMetric](
                metrics=[proc_a, proc_b],
            ),
            disk=MetricsCollection[StorageMetric](metrics=[disk_metric]),
            network=MetricsCollection[NetworkMetric](metrics=[net_metric]),
            gpu=MetricsCollection[GPUMetric](metrics=[gpu_metric]),
            sensors=MetricsCollection[SensorMetric](
                metrics=[sensor_metric],
            ),
            battery=MetricsCollection[BatteryMetric](metrics=[bat_metric]),
            users=MetricsCollection[UserMetric](metrics=[user_metric]),
        )

        result = snapshot_to_system_metrics(snap)

        assert isinstance(result, SystemMetrics)

        # CPU
        assert result.cpu is not None
        assert len(result.cpu.metrics) == 1
        assert result.cpu.metrics[0].usage_percent == 42.5
        assert result.cpu.metrics[0].frequency_mhz == 3500.0

        # RAM
        assert result.ram is not None
        assert len(result.ram.metrics) == 1
        assert result.ram.metrics[0].total_bytes == 8_192_000
        assert result.ram.metrics[0].used_bytes == 4_096_000

        # Processes
        assert result.processes is not None
        assert len(result.processes.metrics) == 2
        assert result.processes.metrics[0].name == "init"
        assert result.processes.metrics[1].name == "test_proc"

        # Storage
        assert result.storage is not None
        assert result.storage.metrics[0].mount_point == "/"

        # Network
        assert result.network is not None
        assert result.network.metrics[0].bytes_sent == 1000

        # GPU
        assert result.gpu is not None
        assert result.gpu.metrics[0].name == "FakeGPU"

        # Sensors
        assert result.sensors is not None
        assert result.sensors.metrics[0].name == "cpu_package"

        # Battery
        assert result.battery is not None
        assert result.battery.metrics[0].percent == 85.0

        # Users
        assert result.users is not None
        assert result.users.metrics[0].name == "testuser"

    # -- Test 2 --------------------------------------------------------

    def test_unavailable_fields_become_empty_collections(self) -> None:
        """Every Unavailable field in the snapshot maps to an empty
        MetricsCollection instead of None.
        """
        snap = TickSnapshot(
            cpu=Unavailable("unsupported", "test"),
            memory=Unavailable("unsupported", "test"),
            processes=Unavailable("unsupported", "test"),
            disk=Unavailable("unsupported", "test"),
            network=Unavailable("unsupported", "test"),
            gpu=Unavailable("unsupported", "test"),
            sensors=Unavailable("unsupported", "test"),
            battery=Unavailable("unsupported", "test"),
            users=Unavailable("unsupported", "test"),
        )

        result = snapshot_to_system_metrics(snap)

        assert isinstance(result, SystemMetrics)

        for field_name in (
            "cpu",
            "ram",
            "processes",
            "storage",
            "network",
            "gpu",
            "sensors",
            "battery",
            "users",
        ):
            collection = getattr(result, field_name)
            assert collection is not None, (
                f"Expected {field_name} to be an empty MetricsCollection, got None"
            )
            assert len(collection.metrics) == 0, (
                f"Expected {field_name} to have 0 metrics, got {len(collection.metrics)}"
            )

    # -- Test 3: partial unavailable -----------------------------------

    def test_partial_unavailable(self) -> None:
        """Only the unavailable fields become empty; available fields
        are preserved.
        """
        snap = TickSnapshot(
            cpu=MetricsCollection[CPUMetric](
                metrics=[CPUMetric(usage_percent=50.0, core_id=None)],
            ),
            memory=Unavailable("unsupported", "no memory"),
            processes=MetricsCollection[ProcessMetric](
                metrics=[
                    ProcessMetric(
                        pid=100,
                        name="bash",
                        cpu_percent=1.0,
                        memory_rss=512,
                        status="running",
                    )
                ],
            ),
            disk=Unavailable("unsupported", "no disk"),
            network=Unavailable("unsupported", "no network"),
            gpu=MetricsCollection[GPUMetric](
                metrics=[
                    GPUMetric(
                        name="RTX",
                        usage_percent=70.0,
                        memory_total=8_000_000,
                        memory_used=4_000_000,
                    )
                ],
            ),
            sensors=Unavailable("unsupported", "no sensors"),
            battery=Unavailable("unsupported", "no battery"),
            users=Unavailable("unsupported", "no users"),
        )

        result = snapshot_to_system_metrics(snap)

        # Available fields keep their data
        assert result.cpu is not None and len(result.cpu.metrics) == 1
        assert result.cpu.metrics[0].usage_percent == 50.0
        assert result.gpu is not None and len(result.gpu.metrics) == 1
        assert result.gpu.metrics[0].name == "RTX"
        assert result.processes is not None and len(result.processes.metrics) == 1
        assert result.processes.metrics[0].pid == 100

        # Unavailable fields become empty collections
        assert result.ram is not None and len(result.ram.metrics) == 0
        assert result.storage is not None and len(result.storage.metrics) == 0
        assert result.network is not None and len(result.network.metrics) == 0
        assert result.sensors is not None and len(result.sensors.metrics) == 0
        assert result.battery is not None and len(result.battery.metrics) == 0
        assert result.users is not None and len(result.users.metrics) == 0


# ===================================================================
# Tests: on_tick_callback
# ===================================================================


class TestOnTickCallback:
    """Exercise the ``BackendEngine`` ``on_tick_callback`` mechanism."""

    # -- Test 3 (from spec) --------------------------------------------

    def test_callback_called_every_tick(self) -> None:
        """``on_tick_callback`` is invoked once per ``tick()`` call."""
        eng, calls = _engine_with_callback()

        assert len(calls) == 0
        eng.tick()
        assert len(calls) == 1, "callback not called after first tick"
        eng.tick()
        assert len(calls) == 2, "callback not called after second tick"
        eng.shutdown()

    # -- Test 4 (from spec) --------------------------------------------

    def test_callback_receives_correct_snapshot(self) -> None:
        """The callback receives the same ``TickSnapshot`` that
        ``tick()`` returns.
        """
        eng, calls = _engine_with_callback()

        returned = eng.tick()
        eng.shutdown()

        assert len(calls) == 1
        recorded = calls[0]

        # Same object identity — the engine passes the snapshot directly
        assert recorded is returned

        # Verify the snapshot has the expected top-level attributes
        for attr in (
            "cpu",
            "memory",
            "processes",
            "disk",
            "network",
            "gpu",
            "sensors",
            "battery",
            "users",
        ):
            assert hasattr(recorded, attr)

        # FakeDriver returns real data for cpu
        assert not isinstance(recorded.cpu, Unavailable)
        # FakeDriver returns Unavailable for disk
        assert isinstance(recorded.disk, Unavailable)

    # -- no callback is fine -------------------------------------------

    def test_engine_works_without_callback(self) -> None:
        """Engine construction and tick succeed when ``on_tick_callback``
        is not provided (the default).
        """
        eng = BackendEngine()
        eng.loader.active_driver = FakeDriver()
        eng.loader.active_scripts = []

        snap = eng.tick()
        eng.shutdown()

        assert isinstance(snap, TickSnapshot)
