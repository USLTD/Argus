from pathlib import Path

from backend.core.sandbox import LuaScriptWrapper
from backend.interfaces.enums import CompatAction, Permission


class TestLuaScriptWrapper:
    def test_metadata_parsed(self, sample_lua_script: Path, compat_ctx, config) -> None:
        script = LuaScriptWrapper.create_if_compatible(
            sample_lua_script, compat_ctx, config
        )
        assert script is not None
        meta = script.METADATA
        assert meta["name"] == "Test Script"
        assert meta["author"] == "Tester"
        assert meta["version"] == "1.0"
        assert meta["permissions"] == [Permission.SCRIPT_READ]  # type: ignore[typeddict-item]

    def test_incompatible_script_returns_none(
        self, tmp_path: Path, compat_ctx, config
    ) -> None:
        path = tmp_path / "incompat.lua"
        path.write_text(
            """
METADATA = {
    name = "Incompat", author = "T", version = "1",
    permissions = {"SCRIPT.READ"},
    compatible = {"sys.platform EQ 'nonexistent' -> TRUE"},
}
argus.events.general.on_tick = function(ctx) end
"""
        )
        cfg_skip = config
        cfg_skip.script_compatibility_default = CompatAction.SKIP
        result = LuaScriptWrapper.create_if_compatible(path, compat_ctx, cfg_skip)
        assert result is None

    def test_compatible_loads(self, tmp_path: Path, compat_ctx, config) -> None:
        path = tmp_path / "compat.lua"
        path.write_text(
            """
METADATA = {
    name = "Compat", author = "T", version = "1",
    permissions = {"SCRIPT.READ"},
    compatible = {"platform.system LIKE '*' -> TRUE"},
}
argus.events.general.on_tick = function(ctx) end
"""
        )
        script = LuaScriptWrapper.create_if_compatible(path, compat_ctx, config)
        assert script is not None
        assert script.METADATA["name"] == "Compat"

    def test_print_captured_in_buffer(
        self, sample_lua_script: Path, compat_ctx, config
    ) -> None:
        script = LuaScriptWrapper.create_if_compatible(
            sample_lua_script, compat_ctx, config
        )
        assert script is not None
        state = {"cpu": {"usage_percent": 50.0}}
        script.execute_tick(state)
        output = script.pop_output()
        assert len(output) == 1
        assert "cpu=50.0" in output[0]

    def test_pop_output_clears_buffer(
        self, sample_lua_script: Path, compat_ctx, config
    ) -> None:
        script = LuaScriptWrapper.create_if_compatible(
            sample_lua_script, compat_ctx, config
        )
        assert script is not None
        script.execute_tick({"cpu": {"usage_percent": 10.0}})
        script.pop_output()
        assert script.pop_output() == []

    def test_dangerous_globals_removed(
        self, sample_lua_script: Path, compat_ctx, config
    ) -> None:
        script = LuaScriptWrapper.create_if_compatible(
            sample_lua_script, compat_ctx, config
        )
        assert script is not None
        g = script.lua.globals()
        for name in ("os", "io", "dofile", "loadfile", "require", "load"):
            assert g[name] is None, f"{name} should be removed"

    def test_kill_process_blocked_without_permission(
        self, tmp_path: Path, compat_ctx, config
    ) -> None:
        path = tmp_path / "no_perm.lua"
        path.write_text(
            """
METADATA = {
    name = "NoPerm", author = "T", version = "1",
    permissions = {"SCRIPT.READ"},
    compatible = {"platform.system LIKE '*' -> TRUE"},
}
argus.events.general.on_tick = function(ctx) end
"""
        )
        script = LuaScriptWrapper.create_if_compatible(path, compat_ctx, config)
        assert script is not None
        result = script.lua.eval("argus.api.kill_process(1234)")
        assert result is False

    def test_permission_validation_rejects_unknown(
        self, tmp_path: Path, compat_ctx, config
    ) -> None:
        path = tmp_path / "bad_perm.lua"
        path.write_text(
            """
METADATA = {
    name = "Bad", author = "T", version = "1",
    permissions = {"INVALID_PERM"},
    compatible = {"platform.system LIKE '*' -> TRUE"},
}
argus.events.general.on_tick = function(ctx) end
"""
        )
        import pytest

        with pytest.raises(ValueError, match="Invalid permission"):
            LuaScriptWrapper.create_if_compatible(path, compat_ctx, config)

    def test_no_compatible_field_defers_to_config_skip(
        self, tmp_path: Path, compat_ctx
    ) -> None:
        path = tmp_path / "no_compat.lua"
        path.write_text(
            """
METADATA = {
    name = "NoCompat", author = "T", version = "1",
    permissions = {"SCRIPT.READ"},
}
argus.events.general.on_tick = function(ctx) end
"""
        )
        from backend.storage.config import ArgusConfig

        cfg = ArgusConfig()
        cfg.script_compatibility_default = CompatAction.SKIP
        result = LuaScriptWrapper.create_if_compatible(path, compat_ctx, cfg)
        assert result is None

    def test_no_compatible_field_defers_to_config_load(
        self, tmp_path: Path, compat_ctx
    ) -> None:
        path = tmp_path / "no_compat_load.lua"
        path.write_text(
            """
METADATA = {
    name = "NoCompatLoad", author = "T", version = "1",
    permissions = {"SCRIPT.READ"},
}
argus.events.general.on_tick = function(ctx) end
"""
        )
        from backend.storage.config import ArgusConfig

        cfg = ArgusConfig()
        cfg.script_compatibility_default = CompatAction.LOAD
        result = LuaScriptWrapper.create_if_compatible(path, compat_ctx, cfg)
        assert result is not None
        assert result.METADATA["name"] == "NoCompatLoad"
