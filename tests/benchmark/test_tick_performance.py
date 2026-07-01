"""Benchmark tests for driver tick latency and converter throughput.

Uses FakeDriver so benchmarks run deterministically without real
hardware.  These benchmarks are meaningful for regression detection
and should NOT be run in CI (they need pinned CPU frequency and
isolated cores for publication-quality numbers).

Usage:
    uv run pytest tests/benchmark/ --benchmark-only
    uv run pytest tests/benchmark/ --benchmark-histogram .hist/
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from backend.bridges.converters import (
    cpu_collection_to_dict,
    memory_collection_to_dict,
    process_collection_to_dict,
)
from backend.interfaces.caps import (
    CPUMetric,
    MemoryMetric,
    MetricMetadata,
    MetricsCollection,
    ProcessMetric,
)
from backend.interfaces.contexts import DriverContext

if TYPE_CHECKING:
    from tests.fake_driver import FakeDriver


# ===================================================================
# Fixtures
# ===================================================================


@pytest.fixture
def driver_ctx() -> DriverContext:
    return DriverContext()


# ===================================================================
# Driver-level benchmarks
# ===================================================================


def test_driver_tick_latency(
    benchmark: pytest.BenchmarkFixture,
    fake_driver: FakeDriver,
    driver_ctx: DriverContext,
) -> None:
    """Measure FakeDriver.tick() latency across 10 iterations.

    This exercises the full aggregate tick (all subsystems) through
    BaseDriver.tick().
    """

    def _tick() -> object:
        return fake_driver.tick(driver_ctx)

    benchmark.extra_info["driver"] = "FakeDriver"
    benchmark.extra_info["iterations"] = 10
    benchmark(_tick)


def test_engine_tick_latency(
    benchmark: pytest.BenchmarkFixture,
    fake_driver: FakeDriver,
) -> None:
    """Measure BackendEngine.tick() latency with FakeDriver injected.

    The engine's normal driver discovery is bypassed by assigning
    FakeDriver directly to active_driver so we measure only the
    engine orchestration overhead + FakeDriver tick.
    """
    from backend.core.engine import BackendEngine

    engine = BackendEngine()
    engine.loader.active_driver = fake_driver

    benchmark.extra_info["driver"] = "FakeDriver (injected into BackendEngine)"
    benchmark(engine.tick)


# ===================================================================
# Per-subsystem latency
# ===================================================================


def test_per_subsystem_latency(
    benchmark: pytest.BenchmarkFixture,
    fake_driver: FakeDriver,
    driver_ctx: DriverContext,
) -> None:
    """Measure each subsystem tick method individually.

    Benchmarks tick_cpu, tick_memory, tick_processes, tick_gpu,
    tick_sensors, tick_battery, tick_disk, tick_network as a
    single grouped run so relative costs are visible.
    """

    def _tick_all_subsystems() -> list[object]:
        return [
            fake_driver.tick_cpu(driver_ctx),
            fake_driver.tick_memory(driver_ctx),
            fake_driver.tick_processes(driver_ctx),
            fake_driver.tick_gpu(driver_ctx),
            fake_driver.tick_sensors(driver_ctx),
            fake_driver.tick_battery(driver_ctx),
            fake_driver.tick_disk(driver_ctx),
            fake_driver.tick_network(driver_ctx),
        ]

    benchmark.extra_info["subsystems"] = (
        "8 (cpu, memory, processes, gpu, sensors, battery, disk, network)"
    )
    benchmark(_tick_all_subsystems)


# ===================================================================
# Bridge-level benchmarks
# ===================================================================


def test_bridge_get_all_latency(
    benchmark: pytest.BenchmarkFixture,
    fake_driver: FakeDriver,
) -> None:
    """Measure SyncBridge.get_all() latency.

    Exercising the full pipeline: tick_all() → per-subsystem
    getters → converter dict construction.
    """
    from backend.bridges.sync_bridge import SyncBridge

    bridge = SyncBridge(fake_driver)

    def _get_all() -> dict:
        return bridge.get_all()

    benchmark.extra_info["bridge"] = "SyncBridge"
    benchmark(_get_all)


# ===================================================================
# Converter throughput
# ===================================================================


def test_converter_throughput(
    benchmark: pytest.BenchmarkFixture,
) -> None:
    """Measure converter dict construction throughput.

    Builds synthetic MetricsCollection objects and runs all three
    major converters (cpu, memory, processes) to measure the pure
    conversion overhead without any driver tick.
    """
    cpu_collection = MetricsCollection[CPUMetric](
        metadata=MetricMetadata(),
        metrics=[
            CPUMetric(usage_percent=42.5, core_id=None),
            CPUMetric(usage_percent=12.3, core_id=0),
            CPUMetric(usage_percent=78.9, core_id=1),
            CPUMetric(usage_percent=55.0, core_id=2),
            CPUMetric(usage_percent=33.3, core_id=3),
        ],
    )
    mem_collection = MetricsCollection[MemoryMetric](
        metadata=MetricMetadata(),
        metrics=[
            MemoryMetric(
                total_bytes=16_000_000_000,
                used_bytes=8_000_000_000,
                available_bytes=8_000_000_000,
                percent=50.0,
            )
        ],
    )
    proc_collection = MetricsCollection[ProcessMetric](
        metadata=MetricMetadata(),
        metrics=[
            ProcessMetric(
                pid=1,
                name="init",
                cpu_percent=0.5,
                memory_rss=2_000_000,
                status="running",
            ),
            ProcessMetric(
                pid=100,
                name="python",
                cpu_percent=15.0,
                memory_rss=50_000_000,
                status="running",
            ),
            ProcessMetric(
                pid=200,
                name="chrome",
                cpu_percent=8.0,
                memory_rss=300_000_000,
                status="running",
            ),
            ProcessMetric(
                pid=300,
                name="sleep",
                cpu_percent=0.0,
                memory_rss=1_000_000,
                status="sleeping",
            ),
        ],
    )

    def _convert_all() -> tuple[dict, dict, list[dict]]:
        return (
            cpu_collection_to_dict(cpu_collection, static_cores=4, static_threads=8),
            memory_collection_to_dict(mem_collection),
            process_collection_to_dict(proc_collection),
        )

    benchmark.extra_info["cpu_metrics"] = "5 (1 aggregate + 4 per-core)"
    benchmark.extra_info["memory_metrics"] = "1"
    benchmark.extra_info["processes"] = "4"
    benchmark(_convert_all)
