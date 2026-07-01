"""Tests for the injector framework and registry."""

from backend.core.injectors import (
    ApiInjector,
    EventInjector,
    all_injectors,
    init_injectors,
    register,
    reset_injectors,
)
from backend.interfaces.enums import Permission


class TestInjectorRegistry:
    def test_registry_initial_state_empty(self) -> None:
        reset_injectors()
        assert all_injectors() == []

    def test_register_and_all(self) -> None:
        reset_injectors()
        inj1 = EventInjector("test.a", ["on_tick"])
        inj2 = EventInjector("test.b", ["on_load"])
        register(inj1)
        register(inj2)
        assert len(all_injectors()) == 2
        assert all_injectors()[0].name == "test_a"
        assert all_injectors()[1].name == "test_b"

    def test_reset_clears(self) -> None:
        reset_injectors()
        register(EventInjector("x", ["y"]))
        assert len(all_injectors()) == 1
        reset_injectors()
        assert all_injectors() == []

    def test_init_injectors_populates(self) -> None:
        reset_injectors()
        init_injectors()
        registry = all_injectors()
        names = {inj.name for inj in registry}
        assert "lifecycle" in names
        assert "events_general" in names
        assert "events_cpu" in names
        assert "events_memory" in names
        assert "events_disk" in names
        assert "events_net" in names
        assert "events_process" in names
        assert "events_gpu" in names
        assert "events_battery" in names
        assert "events_sensor" in names
        assert "api" in names
        assert len(registry) == 12

    def test_init_injectors_idempotent(self) -> None:
        reset_injectors()
        init_injectors()
        count1 = len(all_injectors())
        init_injectors()
        count2 = len(all_injectors())
        assert count1 == count2

    def test_event_injector_permission_gating(self) -> None:
        reset_injectors()
        ro_inj = EventInjector("perm.a", ["on_tick"], permission=Permission.SCRIPT_READ)
        sr_inj = EventInjector("perm.b", ["on_tick"], permission=Permission.SYSTEM_READ)
        assert ro_inj.permission == Permission.SCRIPT_READ
        assert sr_inj.permission == Permission.SYSTEM_READ

    def test_api_injector_no_permission(self) -> None:
        reset_injectors()
        api = ApiInjector()
        assert api.permission is None
        assert api.name == "api"


class TestEventInjector:
    def test_inject_stub_creates_tables(self) -> None:
        from lupa import LuaRuntime

        lua = LuaRuntime(unpack_returned_tuples=True)
        g = lua.globals()
        g["argus"] = lua.table_from({"events": lua.table_from({})})

        inj = EventInjector("events.test", ["on_tick"])
        inj.inject_stub(lua, g["argus"])

        argus = g["argus"]
        assert argus["events"]["test"] is not None

    def test_capture_returns_callbacks(self) -> None:
        from lupa import LuaRuntime

        lua = LuaRuntime(unpack_returned_tuples=True)
        g = lua.globals()
        argus_tbl = lua.table_from({"events": lua.table_from({})})
        g["argus"] = argus_tbl

        inj = EventInjector("events.test", ["on_tick"])
        inj.inject_stub(lua, argus_tbl)

        g["argus"]["events"]["test"]["on_tick"] = lambda x: x

        import types

        wrapper = types.SimpleNamespace()
        callbacks = inj.capture_or_install(lua, argus_tbl, wrapper, set())
        assert "events.test.on_tick" in callbacks

    def test_capture_returns_empty_when_permission_missing(self) -> None:
        from lupa import LuaRuntime

        lua = LuaRuntime(unpack_returned_tuples=True)
        g = lua.globals()
        argus_tbl = lua.table_from({"events": lua.table_from({})})
        g["argus"] = argus_tbl

        inj = EventInjector(
            "events.test", ["on_tick"], permission=Permission.SYSTEM_READ
        )
        inj.inject_stub(lua, argus_tbl)
        g["argus"]["events"]["test"]["on_tick"] = lambda x: x

        import types

        wrapper = types.SimpleNamespace()
        callbacks = inj.capture_or_install(
            lua, argus_tbl, wrapper, {Permission.SCRIPT_READ}
        )
        assert callbacks == {}
