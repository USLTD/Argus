from pathlib import Path

import pytest

from backend.interfaces.enums import CompatAction
from tests.fake_driver import FakeDriver


@pytest.fixture
def fake_driver() -> FakeDriver:
    return FakeDriver()


@pytest.fixture
def compat_ctx():
    from backend.interfaces.rules import build_compat_context

    return build_compat_context()


@pytest.fixture
def config():
    from backend.storage.config import ArgusConfig

    cfg = ArgusConfig()
    cfg.script_compatibility_default = CompatAction.LOAD
    return cfg


@pytest.fixture
def tmp_plugins_dir(tmp_path: Path) -> Path:
    builtin = tmp_path / "drivers" / "builtin"
    builtin.mkdir(parents=True)
    (builtin / "__init__.py").touch()
    return tmp_path


@pytest.fixture
def sample_lua_script(tmp_path: Path) -> Path:
    path = tmp_path / "test_script.lua"
    path.write_text(
        """
METADATA = {
    name = "Test Script",
    author = "Tester",
    version = "1.0",
    permissions = {"SCRIPT.READ_ONLY"},
    compatible = {
        "platform.system LIKE '*' -> TRUE",
    }
}

argus.events.on_tick = function(state)
    print("tick received, cpu=" .. state["cpu"]["usage_percent"])
end
"""
    )
    return path
