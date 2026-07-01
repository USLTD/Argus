"""
Application configuration managed via pydantic-settings backed by a YAML file.

The config file path is resolved by :func:`resolve_config_path()` which respects
the ``ARGUS_CONFIG_PATH`` environment variable (the only way to set the config
location — putting it inside the config itself would be a chicken-and-egg problem).

All fields can be overridden at runtime via environment variables with the
``ARGUS_`` prefix (e.g. ``ARGUS_POLL_INTERVAL_MS=2000``).
"""

from typing import Any

import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict, YamlConfigSettingsSource

from backend.core.paths import resolve_config_path
from backend.interfaces.enums import CompatAction, ScriptExecutionMode

SUBSYSTEM_NAMES: list[str] = [
    "cpu", "memory", "disk", "network", "processes", "gpu", "sensors", "battery", "users"
]


class ArgusConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ARGUS_",
        extra="allow",  # Capture all ARGUS_* env vars, including unknown ones
    )

    driver_override: str | None = None
    poll_interval_ms: int = 1000
    script_compatibility_default: CompatAction = CompatAction.SKIP
    script_batch_size: int = 4
    script_timeout_ms: int = 5000
    script_execution_mode: ScriptExecutionMode = ScriptExecutionMode.NONBLOCKING
    process_tick_interval: int = 5  # Collect processes every N ticks (default 5 = ~5s at 1s poll)
    subsystem_enabled: dict[str, bool] = {
        "cpu": True, "memory": True, "disk": True, "network": True,
        "processes": True, "gpu": True, "sensors": True, "battery": True, "users": True,
    }
    subsystem_intervals: dict[str, int] = {k: 1000 for k in SUBSYSTEM_NAMES}
    subsystem_timeout: dict[str, int] = {k: 5000 for k in SUBSYSTEM_NAMES}

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: Any,
        env_settings: Any,
        dotenv_settings: Any,
        file_secret_settings: Any,
    ) -> tuple[Any, ...]:
        yaml_path = resolve_config_path()
        return (
            init_settings,
            env_settings,
            YamlConfigSettingsSource(settings_cls, yaml_file=yaml_path),
        )

    def save(self) -> None:
        """Write the current configuration back to the YAML file."""
        path = resolve_config_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        data = self.model_dump(mode="json")
        if hasattr(self, "model_extra") and self.model_extra:
            data.update(self.model_extra)
        with path.open("w") as f:
            yaml.dump(data, f)
