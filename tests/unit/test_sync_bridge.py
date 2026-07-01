"""Unit tests for SyncBridge — data shape, auto-tick, and edge cases.

Permission gating is covered separately in test_bridge_permissions.py.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from backend.interfaces.enums import Permission

if TYPE_CHECKING:
    from tests.fake_driver import FakeDriver


# ===================================================================
# Data shape tests
# ===================================================================


class TestSyncBridgeShape:
    """Verify that SyncBridge returns correct data shapes and values."""

    def test_get_cpu_metrics_shape(self, fake_driver: FakeDriver) -> None:
        """get_cpu_metrics returns correct values from FakeDriver.

        FakeDriver returns aggregate 42.5%, no per-core metrics.
        Static info is None (not implemented), so cores are 0.
        """
        from backend.bridges.sync_bridge import SyncBridge

        bridge = SyncBridge(fake_driver)
        data = bridge.get_cpu_metrics()

        assert data["cpu_percent"] == 42.5
        assert data["per_core"] == []
        assert data["frequency"] is None
        assert data["physical_cores"] == 0
        assert data["logical_cores"] == 0

    def test_get_memory_metrics_shape(self, fake_driver: FakeDriver) -> None:
        """get_memory_metrics returns correct values from FakeDriver (50% usage)."""
        from backend.bridges.sync_bridge import SyncBridge

        bridge = SyncBridge(fake_driver)
        data = bridge.get_memory_metrics()

        assert data["total"] == 8192000
        assert data["used"] == 4096000
        assert data["available"] == 4096000
        assert data["percent"] == 50.0

    def test_get_process_list_shape(self, fake_driver: FakeDriver) -> None:
        """get_process_list returns list of dicts with expected keys."""
        from backend.bridges.sync_bridge import SyncBridge

        bridge = SyncBridge(fake_driver)
        procs = bridge.get_process_list()

        assert isinstance(procs, list)
        assert len(procs) == 2

        expected_keys = {"pid", "name", "cpu_percent", "memory_info", "status"}
        for proc in procs:
            assert expected_keys.issubset(proc.keys())

        # FakeDriver returns pid=1 "init" and pid=2 "test_proc"
        names = {p["name"] for p in procs}
        assert "init" in names
        assert "test_proc" in names

    def test_get_battery_shape(self, fake_driver: FakeDriver) -> None:
        """get_battery returns correct values from FakeDriver (85% plugged)."""
        from backend.bridges.sync_bridge import SyncBridge

        bridge = SyncBridge(fake_driver)
        data = bridge.get_battery()

        assert data["percent"] == 85.0
        assert data["power_plugged"] is True
        assert data["seconds_left"] is None

    def test_get_sensors_shape(self, fake_driver: FakeDriver) -> None:
        """get_sensors returns correct values from FakeDriver (cpu_package=65.0)."""
        from backend.bridges.sync_bridge import SyncBridge

        bridge = SyncBridge(fake_driver)
        data = bridge.get_sensors()

        assert "temperatures" in data
        assert data["temperatures"]["cpu_package"] == [65.0]


# ===================================================================
# get_all() contract
# ===================================================================


class TestSyncBridgeGetAll:
    """Verify get_all() returns the full expected dict."""

    def test_get_all_returns_expected_keys(self, fake_driver: FakeDriver) -> None:
        """get_all() includes all 9 top-level keys."""
        from backend.bridges.sync_bridge import SyncBridge

        bridge = SyncBridge(fake_driver)
        data = bridge.get_all()

        expected_keys = {
            "cpu", "memory", "disk", "network", "processes",
            "sensors", "battery", "static_info", "boot_time",
        }
        assert expected_keys.issubset(data.keys())

    def test_get_all_subdicts_have_content(self, fake_driver: FakeDriver) -> None:
        """get_all() returns non-default values for supported subsystems."""
        from backend.bridges.sync_bridge import SyncBridge

        bridge = SyncBridge(fake_driver)
        data = bridge.get_all()

        # CPU has real data
        assert data["cpu"]["cpu_percent"] == 42.5
        # Memory has real data
        assert data["memory"]["total"] == 8192000
        # Battery has real data
        assert data["battery"]["percent"] == 85.0
        # Processes has data
        assert len(data["processes"]) == 2


# ===================================================================
# Static info
# ===================================================================


class TestSyncBridgeStaticInfo:
    """Verify get_static_info() returns a nested dict."""

    def test_get_static_info_returns_nested_dict(self, fake_driver: FakeDriver) -> None:
        """get_static_info returns a dict (possibly empty for FakeDriver)."""
        from backend.bridges.sync_bridge import SyncBridge

        bridge = SyncBridge(fake_driver)
        info = bridge.get_static_info()

        # FakeDriver does not implement _collect_static_info, so
        # BaseDriver.get_static_info() returns None → empty dict
        assert isinstance(info, dict)
        # It may be empty, but it's a plain dict (not None, not a model)
        assert info == {}


# ===================================================================
# Edge cases
# ===================================================================


class TestSyncBridgeEdgeCases:
    """Edge-case tests: initial state, auto-tick, permissions."""

    def test_snapshot_is_none_before_first_tick(self, fake_driver: FakeDriver) -> None:
        """Internal _snapshot is None before any method call."""
        from backend.bridges.sync_bridge import SyncBridge

        bridge = SyncBridge(fake_driver)
        assert bridge._snapshot is None

    def test_auto_tick_consistency(self, fake_driver: FakeDriver) -> None:
        """get_*() works without prior tick_all() — auto-ticks internally.

        This validates the Wave 1 fix: calling any get_* triggers
        tick_all(), so the user never needs to call tick_all() manually.
        """
        from backend.bridges.sync_bridge import SyncBridge

        bridge = SyncBridge(fake_driver)
        # No prior tick_all() call — get_* should auto-tick
        cpu = bridge.get_cpu_metrics()
        assert cpu["cpu_percent"] == 42.5

        mem = bridge.get_memory_metrics()
        assert mem["total"] != 0

        bat = bridge.get_battery()
        assert bat["percent"] == 85.0

    def test_cpu_with_extra_cores_via_static(self, fake_driver: FakeDriver) -> None:
        """CPU cores show static info when driver implements get_static_info.

        After the Wave 1 fix, get_cpu_metrics() fetches static info
        from the driver to populate physical/logical cores.
        FakeDriver does NOT override get_static_info, so cores are 0.
        """
        from backend.bridges.sync_bridge import SyncBridge

        bridge = SyncBridge(fake_driver)
        data = bridge.get_cpu_metrics()
        # BaseDriver.get_static_info() returns None → cores = 0
        assert data["physical_cores"] == 0
        assert data["logical_cores"] == 0
        # Aggregate CPU percent still comes through
        assert data["cpu_percent"] == 42.5

    def test_empty_permissions_blocks_data(self, fake_driver: FakeDriver) -> None:
        """Bridge with empty permissions returns all-zero defaults."""
        from backend.bridges.sync_bridge import SyncBridge

        bridge = SyncBridge(fake_driver, permissions=set())
        cpu = bridge.get_cpu_metrics()
        assert cpu == {
            "cpu_percent": 0.0, "per_core": [], "frequency": None,
            "physical_cores": 0, "logical_cores": 0,
        }
        mem = bridge.get_memory_metrics()
        assert mem == {"total": 0, "used": 0, "available": 0, "free": 0, "cached": 0, "percent": 0.0}
        procs = bridge.get_process_list()
        assert procs == []

    def test_permission_gated_individual_methods(self, fake_driver: FakeDriver) -> None:
        """Only CPU_READ granted returns CPU data, other methods return defaults."""
        from backend.bridges.sync_bridge import SyncBridge

        bridge = SyncBridge(fake_driver, permissions={Permission.CPU_READ})
        cpu = bridge.get_cpu_metrics()
        assert cpu["cpu_percent"] != 0.0
        mem = bridge.get_memory_metrics()
        assert mem["total"] == 0
        disk = bridge.get_disk_usage()
        assert disk["total"] == 0
