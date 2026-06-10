"""
Application configuration managed via pydantic-settings backed by a YAML file.

The config file path is resolved by :func:`resolve_config_path()` which respects
the ``ARGUS_CONFIG_PATH`` environment variable (the only way to set the config
location — putting it inside the config itself would be a chicken-and-egg problem).

All fields can be overridden at runtime via environment variables with the
``ARGUS_`` prefix (e.g. ``ARGUS_THEME=nord``).
"""

from typing import Any

import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict, YamlConfigSettingsSource

from backend.core.paths import resolve_config_path
from backend.interfaces.enums import CompatAction


class ArgusConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ARGUS_",
        extra="ignore",
    )

    theme: str = "default"
    driver_override: str | None = None
    poll_interval_ms: int = 1000
    database_retention_days: int = 30
    script_compatibility_default: CompatAction = CompatAction.SKIP

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
        with path.open("w") as f:
            yaml.dump(self.model_dump(mode="json"), f)
