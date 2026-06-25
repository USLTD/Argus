"""Tests for PythonScriptWrapper."""

from pathlib import Path
from typing import Any


from backend.core.python_script import PythonScriptWrapper
from backend.interfaces.contexts import ScriptContext
from backend.interfaces.plugins import PluginMeta


def _script_ctx() -> ScriptContext[Any]:
    """Minimal ScriptContext for tests that don't need driver/config/db."""
    return ScriptContext[Any](data=None, config=None, db=None, driver=None)


class TestPythonScriptWrapper:
    def test_load_and_extract_hooks_and_events(self, tmp_path: Path) -> None:
        script_path = tmp_path / "test_script.py"
        script_path.write_text(
            """
import argus

@argus.lifecycle.on_load
def setup(ctx):
    print("loaded!")

@argus.events.cpu.on_tick
def on_cpu(ctx):
    print(f"CPU: {ctx.data['usage_percent']}%")

argus.events.memory.on_tick = lambda ctx: print(f"MEM: {ctx.data['percent']}%")
"""
        )
        meta: PluginMeta = {
            "name": "Test",
            "author": "T",
            "version": "1",
            "permissions": [],
        }
        wrapper = PythonScriptWrapper(script_path, meta)

        # Before load — no output
        assert wrapper.pop_output() == []

        # trigger_load should exec and capture lifecycle callback output
        wrapper.trigger_load(_script_ctx())
        output = wrapper.pop_output()
        assert "loaded!" in output

        # Dispatch should work
        wrapper.dispatch("events.cpu.on_tick", {"usage_percent": 42.5})
        output = wrapper.pop_output()
        assert "CPU: 42.5%" in output

        # Assignment-style event
        wrapper.dispatch("events.memory.on_tick", {"percent": 75.0})
        output = wrapper.pop_output()
        assert "MEM: 75.0%" in output

    def test_pop_output_clears(self, tmp_path: Path) -> None:
        script_path = tmp_path / "clear_test.py"
        script_path.write_text(
            """
import argus

@argus.lifecycle.on_load
def setup(ctx):
    print("hello")
"""
        )
        meta: PluginMeta = {
            "name": "Clear",
            "author": "T",
            "version": "1",
            "permissions": [],
        }
        wrapper = PythonScriptWrapper(script_path, meta)
        wrapper.trigger_load(_script_ctx())
        assert wrapper.pop_output() == ["hello"]
        assert wrapper.pop_output() == []

    def test_no_registered_callbacks(self, tmp_path: Path) -> None:
        """Script with no registrations should not error."""
        script_path = tmp_path / "noop.py"
        script_path.write_text(
            """
import argus
x = 42
"""
        )
        meta: PluginMeta = {
            "name": "Noop",
            "author": "T",
            "version": "1",
            "permissions": [],
        }
        wrapper = PythonScriptWrapper(script_path, meta)
        wrapper.trigger_load(_script_ctx())  # should not raise
        wrapper.dispatch("events.cpu.on_tick", {})  # should not raise

    def test_print_captured(self, tmp_path: Path) -> None:
        script_path = tmp_path / "print_test.py"
        script_path.write_text(
            """
import argus

@argus.events.general.on_tick
def on_tick(ctx):
    print("direct")
    argus.api.print("via api")
"""
        )
        meta: PluginMeta = {
            "name": "Print",
            "author": "T",
            "version": "1",
            "permissions": [],
        }
        wrapper = PythonScriptWrapper(script_path, meta)
        wrapper.trigger_load(_script_ctx())
        # trigger_load captured the print from on_load (none), now dispatch
        wrapper.pop_output()  # clear load output
        wrapper.dispatch("events.general.on_tick", {})
        output = wrapper.pop_output()
        assert "direct" in output
        assert "via api" in output
