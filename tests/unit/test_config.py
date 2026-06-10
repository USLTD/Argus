import os
from pathlib import Path

import yaml

from backend.storage.config import ArgusConfig


class TestArgusConfig:
    def test_defaults(self) -> None:
        cfg = ArgusConfig()
        assert cfg.theme == "default"
        assert cfg.driver_override is None
        assert cfg.poll_interval_ms == 1000
        assert cfg.database_retention_days == 30

    def test_env_var_override(self) -> None:
        os.environ["ARGUS_THEME"] = "nord"
        os.environ["ARGUS_POLL_INTERVAL_MS"] = "2000"
        try:
            cfg = ArgusConfig()
            assert cfg.theme == "nord"
            assert cfg.poll_interval_ms == 2000
        finally:
            del os.environ["ARGUS_THEME"]
            del os.environ["ARGUS_POLL_INTERVAL_MS"]

    def test_save_and_reload(self, tmp_path: Path) -> None:
        yaml_path = tmp_path / "test_config.yaml"
        os.environ["ARGUS_CONFIG_PATH"] = str(yaml_path)
        try:
            cfg = ArgusConfig(theme="solarized", poll_interval_ms=500)
            cfg.save()

            assert yaml_path.exists()
            with yaml_path.open() as f:
                data = yaml.safe_load(f)
            assert data["theme"] == "solarized"
            assert data["poll_interval_ms"] == 500
        finally:
            del os.environ["ARGUS_CONFIG_PATH"]
