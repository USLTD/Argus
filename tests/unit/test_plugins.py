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
        methods = ["get_capabilities", "fetch_metrics", "manage_process"]
        for name in methods:
            assert hasattr(BaseDriver, name), f"Missing abstract method: {name}"


class TestBaseUserScript:
    def test_cannot_instantiate(self) -> None:
        with pytest.raises(TypeError):
            BaseUserScript()  # type: ignore[abstract]

    def test_required_method(self) -> None:
        assert hasattr(BaseUserScript, "execute_tick")
