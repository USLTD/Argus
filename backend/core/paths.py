"""
OS-aware path resolution for the application.

Uses standard platform conventions:
- Windows: %APPDATA%\\argus\\ for config, %LOCALAPPDATA%\\argus\\ for data
- Linux/macOS: ~/.config/argus/ for config, ~/.local/share/argus/ for data
"""

import os
import sys
from pathlib import Path


def _get_config_dir() -> Path:
    """Return the platform-appropriate configuration directory."""
    if sys.platform == "win32":
        return (
            Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
            / "argus"
        )
    return Path.home() / ".config" / "argus"


def _get_data_dir() -> Path:
    """Return the platform-appropriate data storage directory."""
    if sys.platform == "win32":
        return (
            Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
            / "argus"
        )
    return Path.home() / ".local" / "share" / "argus"


def resolve_config_path() -> Path:
    """
    Resolve the full path to ``config.yaml``.

    Respects ``ARGUS_CONFIG_PATH`` environment variable for overriding the
    entire config file location. Falls back to the platform default.
    """
    override = os.environ.get("ARGUS_CONFIG_PATH")
    if override:
        return Path(override)
    return _get_config_dir() / "config.yaml"


def resolve_db_path() -> Path:
    """Resolve the full path to the SQLite database file."""
    return _get_data_dir() / "metrics.db"
