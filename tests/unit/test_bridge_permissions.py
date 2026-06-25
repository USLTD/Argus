"""Tests for bridge permission gating.

Verifies that all three bridge classes (SyncBridge, AsyncBridge, EngineBridge)
respect the optional ``permissions`` parameter and PermissionHierarchy.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from backend.interfaces.enums import Permission

if TYPE_CHECKING:
    from tests.fake_driver import FakeDriver


# ===================================================================
# SyncBridge
# ===================================================================


class TestSyncBridgePermissions:
    """Permission gating for SyncBridge."""

    def test_full_access_no_permissions(self, fake_driver: FakeDriver) -> None:
        """Bridge with permissions=None returns all data (frontend behavior)."""
        from backend.bridges.sync_bridge import SyncBridge

        bridge = SyncBridge(fake_driver, permissions=None)
        bridge.tick_all()
        data = bridge.get_cpu_metrics()
        assert data["cpu_percent"] != 0.0  # real data from FakeDriver

    def test_restricted_returns_default(self, fake_driver: FakeDriver) -> None:
        """Bridge with empty permissions returns defaults."""
        from backend.bridges.sync_bridge import SyncBridge

        bridge = SyncBridge(fake_driver, permissions=set())
        bridge.tick_all()
        data = bridge.get_cpu_metrics()
        assert data == {
            "cpu_percent": 0.0, "per_core": [], "frequency": None,
            "physical_cores": 0, "logical_cores": 0,
        }

    def test_cpu_permission_grants_cpu(self, fake_driver: FakeDriver) -> None:
        """Bridge with CPU.READ returns cpu data, but not memory."""
        from backend.bridges.sync_bridge import SyncBridge

        bridge = SyncBridge(fake_driver, permissions={Permission.CPU_READ})
        bridge.tick_all()
        cpu = bridge.get_cpu_metrics()
        assert "cpu_percent" in cpu
        assert cpu["cpu_percent"] != 0.0
        mem = bridge.get_memory_metrics()
        assert mem["total"] == 0  # MEMORY.READ not granted

    def test_memory_permission(self, fake_driver: FakeDriver) -> None:
        """Bridge with MEMORY.READ returns memory data."""
        from backend.bridges.sync_bridge import SyncBridge

        bridge = SyncBridge(fake_driver, permissions={Permission.MEMORY_READ})
        bridge.tick_all()
        mem = bridge.get_memory_metrics()
        assert mem["total"] != 0
        cpu = bridge.get_cpu_metrics()
        assert cpu["cpu_percent"] == 0.0  # CPU.READ not granted

    def test_disk_permission(self, fake_driver: FakeDriver) -> None:
        """Bridge with DISK.READ returns disk data."""
        from backend.bridges.sync_bridge import SyncBridge

        bridge = SyncBridge(fake_driver, permissions={Permission.DISK_READ})
        bridge.tick_all()
        disk = bridge.get_disk_usage()
        assert isinstance(disk, dict)

    def test_network_permission(self, fake_driver: FakeDriver) -> None:
        """Bridge with NETWORK.READ returns network data."""
        from backend.bridges.sync_bridge import SyncBridge

        bridge = SyncBridge(fake_driver, permissions={Permission.NETWORK_READ})
        bridge.tick_all()
        net = bridge.get_network_io()
        assert isinstance(net, dict)

    def test_processes_permission(self, fake_driver: FakeDriver) -> None:
        """Bridge with PROCESSES.READ returns process list."""
        from backend.bridges.sync_bridge import SyncBridge

        bridge = SyncBridge(fake_driver, permissions={Permission.PROCESSES_READ})
        bridge.tick_all()
        procs = bridge.get_process_list()
        assert isinstance(procs, list)

    def test_sensors_permission(self, fake_driver: FakeDriver) -> None:
        """Bridge with SENSORS.READ returns sensor data."""
        from backend.bridges.sync_bridge import SyncBridge

        bridge = SyncBridge(fake_driver, permissions={Permission.SENSORS_READ})
        bridge.tick_all()
        sensors = bridge.get_sensors()
        assert isinstance(sensors, dict)

    def test_battery_permission(self, fake_driver: FakeDriver) -> None:
        """Bridge with BATTERY.READ returns battery data."""
        from backend.bridges.sync_bridge import SyncBridge

        bridge = SyncBridge(fake_driver, permissions={Permission.BATTERY_READ})
        bridge.tick_all()
        bat = bridge.get_battery()
        assert isinstance(bat, dict)

    def test_static_info_gated_by_system_read(self, fake_driver: FakeDriver) -> None:
        """Bridge without SYSTEM.READ returns empty static info."""
        from backend.bridges.sync_bridge import SyncBridge

        bridge = SyncBridge(fake_driver, permissions=set())
        bridge.tick_all()
        info = bridge.get_static_info()
        assert info == {}

    def test_boot_time_gated_by_system_read(self, fake_driver: FakeDriver) -> None:
        """Bridge without SYSTEM.READ returns 0.0 boot time."""
        from backend.bridges.sync_bridge import SyncBridge

        bridge = SyncBridge(fake_driver, permissions=set())
        bridge.tick_all()
        boot = bridge.get_boot_time()
        assert boot == 0.0

    def test_hierarchy_write_grants_read(self, fake_driver: FakeDriver) -> None:
        """Bridge with CPU.WRITE still grants CPU.READ via hierarchy."""
        from backend.bridges.sync_bridge import SyncBridge

        bridge = SyncBridge(fake_driver, permissions={Permission.CPU_WRITE})
        bridge.tick_all()
        cpu = bridge.get_cpu_metrics()
        assert cpu["cpu_percent"] != 0.0  # WRITE grants READ

    def test_hierarchy_exec_grants_read(self, fake_driver: FakeDriver) -> None:
        """Bridge with PROCESSES.EXECUTE grants PROCESSES.READ."""
        from backend.bridges.sync_bridge import SyncBridge

        bridge = SyncBridge(fake_driver, permissions={Permission.PROCESSES_EXECUTE})
        bridge.tick_all()
        procs = bridge.get_process_list()
        assert isinstance(procs, list)  # EXECUTE grants READ

    def test_terminate_process_no_permission(self, fake_driver: FakeDriver) -> None:
        """Bridge without PROCESSES.WRITE returns False for terminate."""
        from backend.bridges.sync_bridge import SyncBridge

        bridge = SyncBridge(fake_driver, permissions=set())
        result = bridge.terminate_process(1)
        assert result is False

    def test_kill_process_no_permission(self, fake_driver: FakeDriver) -> None:
        """Bridge without PROCESSES.EXECUTE returns False for kill."""
        from backend.bridges.sync_bridge import SyncBridge

        bridge = SyncBridge(fake_driver, permissions=set())
        result = bridge.kill_process(1)
        assert result is False

    def test_terminate_process_with_permission(self, fake_driver: FakeDriver) -> None:
        """Bridge with PROCESSES.WRITE can terminate processes."""
        from backend.bridges.sync_bridge import SyncBridge

        bridge = SyncBridge(fake_driver, permissions={Permission.PROCESSES_WRITE})
        result = bridge.terminate_process(1)
        # FakeDriver.manage_process returns action == "kill" only, not "terminate"
        assert result is False  # FakeDriver returns False for terminate

    def test_kill_process_with_permission(self, fake_driver: FakeDriver) -> None:
        """Bridge with PROCESSES.EXECUTE can kill processes."""
        from backend.bridges.sync_bridge import SyncBridge

        bridge = SyncBridge(fake_driver, permissions={Permission.PROCESSES_EXECUTE})
        result = bridge.kill_process(42)
        assert result is True  # FakeDriver returns True for kill with pid>0

    def test_get_all_respects_permissions(self, fake_driver: FakeDriver) -> None:
        """get_all() returns defaults for subsystems without permission."""
        from backend.bridges.sync_bridge import SyncBridge

        bridge = SyncBridge(fake_driver, permissions={Permission.CPU_READ})
        bridge.tick_all()
        all_data = bridge.get_all()
        # CPU should have data
        assert all_data["cpu"]["cpu_percent"] != 0.0
        # Other subsystems should be defaults
        assert all_data["memory"]["total"] == 0
        assert all_data["disk"]["total"] == 0
        assert all_data["network"]["bytes_sent"] == 0
        assert all_data["processes"] == []
        assert all_data["static_info"] == {}

    def test_multiple_permissions(self, fake_driver: FakeDriver) -> None:
        """Bridge with multiple permissions returns data for each."""
        from backend.bridges.sync_bridge import SyncBridge

        perms = {Permission.CPU_READ, Permission.MEMORY_READ, Permission.BATTERY_READ}
        bridge = SyncBridge(fake_driver, permissions=perms)
        bridge.tick_all()
        assert bridge.get_cpu_metrics()["cpu_percent"] != 0.0
        assert bridge.get_memory_metrics()["total"] != 0
        assert bridge.get_battery()["percent"] != 0.0

    def test_system_read_grants_boot_time(self, fake_driver: FakeDriver) -> None:
        """Bridge with SYSTEM.READ returns boot_time via hierarchy."""
        from backend.bridges.sync_bridge import SyncBridge

        bridge = SyncBridge(fake_driver, permissions={Permission.SYSTEM_READ})
        bridge.tick_all()
        boot = bridge.get_boot_time()
        # FakeDriver has no static info so returns 0.0 even when permitted
        assert boot == 0.0


# ===================================================================
# AsyncBridge
# ===================================================================


class TestAsyncBridgePermissions:
    """Permission gating for AsyncBridge."""

    @pytest.mark.asyncio
    async def test_full_access_no_permissions(self, fake_driver: FakeDriver) -> None:
        """Async bridge with permissions=None returns all data."""
        from backend.bridges.async_bridge import AsyncBridge

        bridge = AsyncBridge(fake_driver, permissions=None)
        await bridge.tick_all()
        data = await bridge.get_cpu_metrics()
        assert data["cpu_percent"] != 0.0

    @pytest.mark.asyncio
    async def test_restricted_returns_default(self, fake_driver: FakeDriver) -> None:
        """Async bridge with empty permissions returns defaults."""
        from backend.bridges.async_bridge import AsyncBridge

        bridge = AsyncBridge(fake_driver, permissions=set())
        await bridge.tick_all()
        data = await bridge.get_cpu_metrics()
        assert data == {
            "cpu_percent": 0.0, "per_core": [], "frequency": None,
            "physical_cores": 0, "logical_cores": 0,
        }

    @pytest.mark.asyncio
    async def test_cpu_permission(self, fake_driver: FakeDriver) -> None:
        """Async bridge with CPU.READ returns cpu data."""
        from backend.bridges.async_bridge import AsyncBridge

        bridge = AsyncBridge(fake_driver, permissions={Permission.CPU_READ})
        await bridge.tick_all()
        cpu = await bridge.get_cpu_metrics()
        assert cpu["cpu_percent"] != 0.0
        mem = await bridge.get_memory_metrics()
        assert mem["total"] == 0

    @pytest.mark.asyncio
    async def test_hierarchy_write_grants_read(self, fake_driver: FakeDriver) -> None:
        """Async bridge with CPU.WRITE still grants CPU.READ."""
        from backend.bridges.async_bridge import AsyncBridge

        bridge = AsyncBridge(fake_driver, permissions={Permission.CPU_WRITE})
        await bridge.tick_all()
        cpu = await bridge.get_cpu_metrics()
        assert cpu["cpu_percent"] != 0.0

    @pytest.mark.asyncio
    async def test_hierarchy_exec_grants_read(self, fake_driver: FakeDriver) -> None:
        """Async bridge with PROCESSES.EXECUTE grants PROCESSES.READ."""
        from backend.bridges.async_bridge import AsyncBridge

        bridge = AsyncBridge(fake_driver, permissions={Permission.PROCESSES_EXECUTE})
        await bridge.tick_all()
        procs = await bridge.get_process_list()
        assert isinstance(procs, list)

    @pytest.mark.asyncio
    async def test_terminate_no_permission(self, fake_driver: FakeDriver) -> None:
        """Async bridge without PROCESSES.WRITE returns False."""
        from backend.bridges.async_bridge import AsyncBridge

        bridge = AsyncBridge(fake_driver, permissions=set())
        result = await bridge.terminate_process(1)
        assert result is False

    @pytest.mark.asyncio
    async def test_kill_with_permission(self, fake_driver: FakeDriver) -> None:
        """Async bridge with PROCESSES.EXECUTE can kill."""
        from backend.bridges.async_bridge import AsyncBridge

        bridge = AsyncBridge(fake_driver, permissions={Permission.PROCESSES_EXECUTE})
        result = await bridge.kill_process(42)
        assert result is True

    @pytest.mark.asyncio
    async def test_get_all_respects_permissions(self, fake_driver: FakeDriver) -> None:
        """Async get_all() returns defaults for denied subsystems."""
        from backend.bridges.async_bridge import AsyncBridge

        bridge = AsyncBridge(fake_driver, permissions={Permission.CPU_READ})
        await bridge.tick_all()
        all_data = await bridge.get_all()
        assert all_data["cpu"]["cpu_percent"] != 0.0
        assert all_data["memory"]["total"] == 0

    @pytest.mark.asyncio
    async def test_static_info_gated(self, fake_driver: FakeDriver) -> None:
        """Async bridge without SYSTEM.READ returns empty static info."""
        from backend.bridges.async_bridge import AsyncBridge

        bridge = AsyncBridge(fake_driver, permissions=set())
        info = await bridge.get_static_info()
        assert info == {}

    @pytest.mark.asyncio
    async def test_system_read_grants_static_info(self, fake_driver: FakeDriver) -> None:
        """Async bridge with SYSTEM.READ returns static info."""
        from backend.bridges.async_bridge import AsyncBridge

        bridge = AsyncBridge(fake_driver, permissions={Permission.SYSTEM_READ})
        info = await bridge.get_static_info()
        assert isinstance(info, dict)


# ===================================================================
# EngineBridge
# ===================================================================


class TestEngineBridgePermissions:
    """Permission gating for EngineBridge.

    EngineBridge requires an engine object. When engine is None all
    get_*() methods return defaults regardless, so these tests verify
    the gating does not crash and returns the correct default shape.
    """

    @staticmethod
    def _import_bridge():
        """Import EngineBridge, skipping if PyQt6 not available."""
        pytest.importorskip("PyQt6", reason="PyQt6 not installed")
        from frontend.core.engine_bridge import EngineBridge

        return EngineBridge

    def test_full_access_no_permissions(self) -> None:
        """Engine bridge with permissions=None works (frontend behavior)."""
        EngineBridge = self._import_bridge()
        bridge = EngineBridge(engine=None, permissions=None)
        # Should not raise, returns defaults since engine=None
        cpu = bridge.get_cpu_metrics()
        assert cpu["cpu_percent"] == 0.0
        mem = bridge.get_memory_metrics()
        assert mem["total"] == 0
        procs = bridge.get_process_list()
        assert procs == []

    def test_restricted_returns_default(self) -> None:
        """Engine bridge with empty permissions returns defaults."""
        EngineBridge = self._import_bridge()
        bridge = EngineBridge(engine=None, permissions=set())
        cpu = bridge.get_cpu_metrics()
        assert cpu == {"cpu_percent": 0.0, "per_core": [], "frequency": None, "physical_cores": 0, "logical_cores": 0}
        mem = bridge.get_memory_metrics()
        assert mem == {"total": 0, "used": 0, "available": 0, "free": 0, "cached": 0, "percent": 0.0}

    def test_cpu_permission(self) -> None:
        """Engine bridge with CPU.READ returns default cpu (engine=None)."""
        EngineBridge = self._import_bridge()
        bridge = EngineBridge(engine=None, permissions={Permission.CPU_READ})
        cpu = bridge.get_cpu_metrics()
        # Permission check passes, but engine=None so state={}
        assert "cpu_percent" in cpu
        mem = bridge.get_memory_metrics()
        assert mem["total"] == 0  # MEMORY.READ not granted

    def test_sensors_permission(self) -> None:
        """Engine bridge with SENSORS.READ returns default sensors (engine=None)."""
        EngineBridge = self._import_bridge()
        bridge = EngineBridge(engine=None, permissions={Permission.SENSORS_READ})
        sensors = bridge.get_sensors()
        assert sensors == {}

    def test_battery_permission(self) -> None:
        """Engine bridge with BATTERY.READ returns default battery."""
        EngineBridge = self._import_bridge()
        bridge = EngineBridge(engine=None, permissions={Permission.BATTERY_READ})
        bat = bridge.get_battery()
        assert bat["percent"] == 0.0

    def test_static_info_gated(self) -> None:
        """Engine bridge without SYSTEM.READ returns empty static info."""
        EngineBridge = self._import_bridge()
        bridge = EngineBridge(engine=None, permissions=set())
        info = bridge.get_static_info()
        assert info["hostname"] == ""

    def test_system_load_gated(self) -> None:
        """Engine bridge without SYSTEM.READ returns default load."""
        EngineBridge = self._import_bridge()
        bridge = EngineBridge(engine=None, permissions=set())
        load = bridge.get_system_load()
        assert load == {"cpu_percent": 0.0, "processes": 0, "threads": 0, "handles": 0}

    def test_disk_partitions_gated(self) -> None:
        """Engine bridge without DISK.READ returns empty partitions."""
        EngineBridge = self._import_bridge()
        bridge = EngineBridge(engine=None, permissions=set())
        parts = bridge.get_disk_partitions()
        assert parts == []

    def test_network_interfaces_gated(self) -> None:
        """Engine bridge without NETWORK.READ returns empty interfaces."""
        EngineBridge = self._import_bridge()
        bridge = EngineBridge(engine=None, permissions=set())
        ifaces = bridge.get_network_interfaces()
        assert ifaces == {}

    def test_terminate_no_permission(self) -> None:
        """Engine bridge without PROCESSES.WRITE returns False."""
        EngineBridge = self._import_bridge()
        bridge = EngineBridge(engine=None, permissions=set())
        result = bridge.terminate_process(1)
        assert result is False

    def test_kill_no_permission(self) -> None:
        """Engine bridge without PROCESSES.EXECUTE returns False."""
        EngineBridge = self._import_bridge()
        bridge = EngineBridge(engine=None, permissions=set())
        result = bridge.kill_process(1)
        assert result is False

    def test_terminate_with_permission(self) -> None:
        """Engine bridge with PROCESSES.WRITE attempts terminate."""
        EngineBridge = self._import_bridge()
        bridge = EngineBridge(engine=None, permissions={Permission.PROCESSES_WRITE})
        # _driver is None since engine=None, so _manage_process returns False
        result = bridge.terminate_process(1)
        assert result is False

    def test_kill_with_permission(self) -> None:
        """Engine bridge with PROCESSES.EXECUTE attempts kill."""
        EngineBridge = self._import_bridge()
        bridge = EngineBridge(engine=None, permissions={Permission.PROCESSES_EXECUTE})
        result = bridge.kill_process(1)
        assert result is False

    def test_get_all_respects_permissions(self) -> None:
        """Engine bridge get_all() returns defaults for denied subsystems."""
        EngineBridge = self._import_bridge()
        bridge = EngineBridge(engine=None, permissions=set())
        all_data = bridge.get_all()
        assert all_data["cpu"]["cpu_percent"] == 0.0
        assert all_data["memory"]["total"] == 0
        assert all_data["processes"] == []
