from pathlib import Path

from backend.core.loader import DiscoveryLoader


class TestDiscoveryLoader:
    def test_auto_creates_custom_dir(self, tmp_plugins_dir: Path) -> None:
        custom = tmp_plugins_dir / "drivers" / "custom"
        assert not custom.exists()
        loader = DiscoveryLoader(str(tmp_plugins_dir))
        loader.soft_reload()
        assert custom.exists()
        assert (custom / "__init__.py").exists()

    def test_no_drivers_returns_none(self, tmp_plugins_dir: Path) -> None:
        loader = DiscoveryLoader(str(tmp_plugins_dir))
        loader.soft_reload()
        assert loader.active_driver is None
        assert loader.all_candidates == []

    def test_ranks_highest_score(self, tmp_path: Path, compat_ctx) -> None:
        builtin = tmp_path / "drivers" / "builtin"
        builtin.mkdir(parents=True)
        (builtin / "__init__.py").touch()

        (builtin / "high_score.py").write_text(
            """
from backend.interfaces.plugins import BaseDriver, PluginMeta
from backend.interfaces.enums import ConfidenceScore, Permission
from backend.interfaces.caps import SystemCapabilities, SystemMetrics, CPUMetrics, RAMMetrics

METADATA: PluginMeta = {
    "name": "High",
    "author": "T",
    "version": "1",
    "permissions": [],
    "compatible": lambda ctx: ConfidenceScore.FULL,
}

class HighScore(BaseDriver):
    def get_capabilities(self): return SystemCapabilities()
    def on_tick(self):
        return SystemMetrics(cpu=CPUMetrics(physical_cores=1,logical_cores=1,usage_percent=0),
                             ram=RAMMetrics(total_bytes=1,used_bytes=0,available_bytes=1,percent=0))
    def manage_process(self, pid, action, **kw): return False

DRIVER = HighScore
"""
        )
        (builtin / "low_score.py").write_text(
            """
from backend.interfaces.plugins import BaseDriver, PluginMeta
from backend.interfaces.enums import ConfidenceScore, Permission
from backend.interfaces.caps import SystemCapabilities, SystemMetrics, CPUMetrics, RAMMetrics

METADATA: PluginMeta = {
    "name": "Low",
    "author": "T",
    "version": "1",
    "permissions": [],
    "compatible": lambda ctx: ConfidenceScore.LOW,
}

class LowScore(BaseDriver):
    def get_capabilities(self): return SystemCapabilities()
    def on_tick(self):
        return SystemMetrics(cpu=CPUMetrics(physical_cores=1,logical_cores=1,usage_percent=0),
                             ram=RAMMetrics(total_bytes=1,used_bytes=0,available_bytes=1,percent=0))
    def manage_process(self, pid, action, **kw): return False

DRIVER = LowScore
"""
        )
        loader = DiscoveryLoader(str(tmp_path))
        loader.soft_reload(compat_ctx=compat_ctx)
        assert loader.active_driver is not None
        high = [c for c in loader.all_candidates if c.meta["name"] == "High"]
        assert len(high) == 1
        assert high[0].loaded is True
        assert len(loader.all_candidates) == 2

    def test_candidates_tracked(self, tmp_plugins_dir: Path, compat_ctx) -> None:
        custom = tmp_plugins_dir / "drivers" / "custom"
        custom.mkdir(parents=True)
        (custom / "__init__.py").touch()
        (custom / "test_driver.py").write_text(
            """
from backend.interfaces.plugins import BaseDriver, PluginMeta
from backend.interfaces.enums import ConfidenceScore, Permission
from backend.interfaces.caps import SystemCapabilities, SystemMetrics, CPUMetrics, RAMMetrics

METADATA: PluginMeta = {
    "name": "CT",
    "author": "T",
    "version": "1",
    "permissions": [],
    "compatible": lambda ctx: ConfidenceScore.MEDIUM,
}

class CustomTest(BaseDriver):
    def get_capabilities(self): return SystemCapabilities()
    def on_tick(self):
        return SystemMetrics(cpu=CPUMetrics(physical_cores=1,logical_cores=1,usage_percent=0),
                             ram=RAMMetrics(total_bytes=1,used_bytes=0,available_bytes=1,percent=0))
    def manage_process(self, pid, action, **kw): return False

DRIVER = CustomTest
"""
        )
        loader = DiscoveryLoader(str(tmp_plugins_dir))
        loader.soft_reload(compat_ctx=compat_ctx)
        assert len(loader.all_candidates) >= 1
        names = [c.meta["name"] for c in loader.all_candidates]
        assert "CT" in names
