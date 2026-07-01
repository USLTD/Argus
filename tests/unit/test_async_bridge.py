"""Unit tests for AsyncBridge — data shape, auto-tick, polling lifecycle, and edge cases.

Permission gating is covered separately in test_bridge_permissions.py.
All tests are marked with @pytest.mark.asyncio.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest

from backend.interfaces.enums import Permission

if TYPE_CHECKING:
    from tests.fake_driver import FakeDriver


# ===================================================================
# Data shape tests
# ===================================================================


class TestAsyncBridgeShape:
    """Verify that AsyncBridge returns correct data shapes and values."""

    @pytest.mark.asyncio
    async def test_get_cpu_metrics_shape(self, fake_driver: FakeDriver) -> None:
        """get_cpu_metrics returns correct values from FakeDriver."""
        from backend.bridges.async_bridge import AsyncBridge

        bridge = AsyncBridge(fake_driver)
        data = await bridge.get_cpu_metrics()

        assert data["cpu_percent"] == 42.5
        assert data["per_core"] == []
        assert data["frequency"] is None
        assert data["physical_cores"] == 0
        assert data["logical_cores"] == 0

    @pytest.mark.asyncio
    async def test_get_memory_metrics_shape(self, fake_driver: FakeDriver) -> None:
        """get_memory_metrics returns correct values from FakeDriver (50% usage)."""
        from backend.bridges.async_bridge import AsyncBridge

        bridge = AsyncBridge(fake_driver)
        data = await bridge.get_memory_metrics()

        assert data["total"] == 8192000
        assert data["used"] == 4096000
        assert data["available"] == 4096000
        assert data["percent"] == 50.0

    @pytest.mark.asyncio
    async def test_get_process_list_shape(self, fake_driver: FakeDriver) -> None:
        """get_process_list returns list of dicts with expected keys."""
        from backend.bridges.async_bridge import AsyncBridge

        bridge = AsyncBridge(fake_driver)
        procs = await bridge.get_process_list()

        assert isinstance(procs, list)
        assert len(procs) == 2

        expected_keys = {"pid", "name", "cpu_percent", "memory_info", "status"}
        for proc in procs:
            assert expected_keys.issubset(proc.keys())

        names = {p["name"] for p in procs}
        assert "init" in names
        assert "test_proc" in names

    @pytest.mark.asyncio
    async def test_get_battery_shape(self, fake_driver: FakeDriver) -> None:
        """get_battery returns correct values from FakeDriver (85% plugged)."""
        from backend.bridges.async_bridge import AsyncBridge

        bridge = AsyncBridge(fake_driver)
        data = await bridge.get_battery()

        assert data["percent"] == 85.0
        assert data["power_plugged"] is True
        assert data["seconds_left"] is None

    @pytest.mark.asyncio
    async def test_get_sensors_shape(self, fake_driver: FakeDriver) -> None:
        """get_sensors returns correct values from FakeDriver."""
        from backend.bridges.async_bridge import AsyncBridge

        bridge = AsyncBridge(fake_driver)
        data = await bridge.get_sensors()

        assert "temperatures" in data
        assert data["temperatures"]["cpu_package"] == [65.0]


# ===================================================================
# get_all() contract
# ===================================================================


class TestAsyncBridgeGetAll:
    """Verify async get_all() returns the full expected dict."""

    @pytest.mark.asyncio
    async def test_get_all_returns_expected_keys(self, fake_driver: FakeDriver) -> None:
        """get_all() includes all 7 top-level keys (async bridge has no static_info or boot_time)."""
        from backend.bridges.async_bridge import AsyncBridge

        bridge = AsyncBridge(fake_driver)
        data = await bridge.get_all()

        expected_keys = {
            "cpu", "memory", "disk", "network",
            "processes", "sensors", "battery",
        }
        assert expected_keys.issubset(data.keys())

    @pytest.mark.asyncio
    async def test_get_all_subdicts_have_content(self, fake_driver: FakeDriver) -> None:
        """get_all() returns non-default values for supported subsystems."""
        from backend.bridges.async_bridge import AsyncBridge

        bridge = AsyncBridge(fake_driver)
        data = await bridge.get_all()

        assert data["cpu"]["cpu_percent"] == 42.5
        assert data["memory"]["total"] == 8192000
        assert data["battery"]["percent"] == 85.0
        assert len(data["processes"]) == 2


# ===================================================================
# Static info
# ===================================================================


class TestAsyncBridgeStaticInfo:
    """Verify async get_static_info() returns a nested dict."""

    @pytest.mark.asyncio
    async def test_get_static_info_returns_nested_dict(self, fake_driver: FakeDriver) -> None:
        """get_static_info returns a dict (FakeDriver returns None → empty dict)."""
        from backend.bridges.async_bridge import AsyncBridge

        bridge = AsyncBridge(fake_driver)
        info = await bridge.get_static_info()

        assert isinstance(info, dict)
        assert info == {}


# ===================================================================
# Polling lifecycle
# ===================================================================


class TestAsyncBridgePolling:
    """Verify start_polling / stop_polling lifecycle."""

    @pytest.mark.asyncio
    async def test_start_polling_creates_task(self, fake_driver: FakeDriver) -> None:
        """start_polling creates a background task and snapshot gets populated."""
        from backend.bridges.async_bridge import AsyncBridge

        bridge = AsyncBridge(fake_driver)
        assert bridge._poll_task is None
        assert bridge.snapshot is None

        await bridge.start_polling(interval=0.05)  # very short interval
        assert bridge._poll_task is not None
        assert not bridge._poll_task.done()

        # Give the task time to run one tick
        await asyncio.sleep(0.1)
        assert bridge.snapshot is not None

        await bridge.stop_polling()
        assert bridge._poll_task is None

    @pytest.mark.asyncio
    async def test_stop_polling_cancels_task(self, fake_driver: FakeDriver) -> None:
        """stop_polling cancels the background task."""
        from backend.bridges.async_bridge import AsyncBridge

        bridge = AsyncBridge(fake_driver)
        await bridge.start_polling(interval=2.0)
        assert bridge._poll_task is not None

        await bridge.stop_polling()
        assert bridge._poll_task is None

    @pytest.mark.asyncio
    async def test_start_polling_twice_is_noop(self, fake_driver: FakeDriver) -> None:
        """Calling start_polling twice does not create a second task."""
        from backend.bridges.async_bridge import AsyncBridge

        bridge = AsyncBridge(fake_driver)
        await bridge.start_polling(interval=2.0)
        task_1 = bridge._poll_task

        await bridge.start_polling(interval=2.0)
        task_2 = bridge._poll_task

        # Same task object — no duplicate created
        assert task_1 is task_2

        await bridge.stop_polling()


# ===================================================================
# Edge cases
# ===================================================================


class TestAsyncBridgeEdgeCases:
    """Edge-case tests: initial state, auto-tick, permissions."""

    @pytest.mark.asyncio
    async def test_snapshot_is_none_before_first_tick(self, fake_driver: FakeDriver) -> None:
        """Internal _snapshot is None and snapshot property returns None before any tick."""
        from backend.bridges.async_bridge import AsyncBridge

        bridge = AsyncBridge(fake_driver)
        assert bridge._snapshot is None
        assert bridge.snapshot is None

    @pytest.mark.asyncio
    async def test_auto_tick_consistency(self, fake_driver: FakeDriver) -> None:
        """get_*() works without prior tick_all() — auto-ticks internally.

        This validates the Wave 1 fix: calling any async get_* triggers
        tick_all(), so the user never needs to call tick_all() manually.
        """
        from backend.bridges.async_bridge import AsyncBridge

        bridge = AsyncBridge(fake_driver)
        # No prior tick_all() — get_* should auto-tick
        cpu = await bridge.get_cpu_metrics()
        assert cpu["cpu_percent"] == 42.5

        mem = await bridge.get_memory_metrics()
        assert mem["total"] != 0

        bat = await bridge.get_battery()
        assert bat["percent"] == 85.0

    @pytest.mark.asyncio
    async def test_empty_permissions_blocks_data(self, fake_driver: FakeDriver) -> None:
        """Bridge with empty permissions returns all-zero defaults."""
        from backend.bridges.async_bridge import AsyncBridge

        bridge = AsyncBridge(fake_driver, permissions=set())
        cpu = await bridge.get_cpu_metrics()
        assert cpu == {
            "cpu_percent": 0.0, "per_core": [], "frequency": None,
            "physical_cores": 0, "logical_cores": 0,
        }
        mem = await bridge.get_memory_metrics()
        assert mem == {"total": 0, "used": 0, "available": 0, "free": 0, "cached": 0, "percent": 0.0}
        procs = await bridge.get_process_list()
        assert procs == []

    @pytest.mark.asyncio
    async def test_permission_gated_individual_methods(self, fake_driver: FakeDriver) -> None:
        """Only CPU_READ granted returns CPU data, other methods return defaults."""
        from backend.bridges.async_bridge import AsyncBridge

        bridge = AsyncBridge(fake_driver, permissions={Permission.CPU_READ})
        cpu = await bridge.get_cpu_metrics()
        assert cpu["cpu_percent"] != 0.0
        mem = await bridge.get_memory_metrics()
        assert mem["total"] == 0
