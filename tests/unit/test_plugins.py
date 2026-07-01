import pytest

from backend.interfaces.plugins import BaseDriver, BasePlugin, BaseUserScript


class TestBasePlugin:
    def test_can_instantiate_marker(self) -> None:
        instance = BasePlugin()  # no abstract methods → allowed
        assert isinstance(instance, BasePlugin)


class TestBaseDriver:
    def test_cannot_instantiate(self) -> None:
        with pytest.raises(TypeError):
            BaseDriver()  # type: ignore[abstract]

    def test_required_methods(self) -> None:
        methods = ["get_capabilities", "tick", "manage_process"]
        for name in methods:
            assert hasattr(BaseDriver, name), f"Missing abstract method: {name}"


class TestBaseUserScript:
    def test_can_instantiate(self) -> None:
        """BaseUserScript has no abstract methods — all hooks are optional no-ops."""
        instance = BaseUserScript()
        assert isinstance(instance, BaseUserScript)

    def test_required_methods(self) -> None:
        methods = [
            "bind_driver",
            "trigger_load",
            "trigger_unload",
            "dispatch",
            "pop_output",
        ]
        for name in methods:
            assert hasattr(BaseUserScript, name), f"Missing method: {name}"
