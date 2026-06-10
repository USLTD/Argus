"""
Discovery Loader for resolving Python Drivers and Lua Scripts.
"""

import importlib.util
import sys
from pathlib import Path
from typing import Any, Optional

from backend.core.sandbox import LuaScriptWrapper
from backend.interfaces.enums import ConfidenceScore
from backend.interfaces.plugins import BaseDriver, BaseUserScript, PluginMeta
from backend.interfaces.rules import evaluate_compatible


class DriverCandidate:
    """Describes a single driver discovered during the last scan."""

    def __init__(
        self,
        cls: type[BaseDriver],
        score: ConfidenceScore,
        file_path: Path,
        meta: PluginMeta,
        loaded: bool = False,
    ) -> None:
        self.cls = cls
        self.score = score
        self.file_path = file_path
        self.meta = meta
        self.loaded = loaded


class DiscoveryLoader:
    def __init__(self, plugins_dir: str = ".") -> None:
        self.root_dir = Path(plugins_dir)
        self.active_driver: Optional[BaseDriver] = None
        self.active_scripts: list[BaseUserScript] = []
        self.all_candidates: list[DriverCandidate] = []

    def soft_reload(self, compat_ctx: Any = None, config: Any = None) -> None:
        """Flush cache and reload highest-ranked driver and all compatible scripts."""
        self.active_scripts.clear()
        self.all_candidates.clear()

        driver_dirs = [
            self.root_dir / "drivers" / "builtin",
            self.root_dir / "drivers" / "custom",
        ]

        for mod in list(sys.modules.keys()):
            if mod.startswith("dynamic_driver_"):
                del sys.modules[mod]

        best_score = ConfidenceScore.INCOMPATIBLE
        best_module: Any = None
        best_cls: type[BaseDriver] | None = None

        # 1. Load Drivers
        for driver_dir in driver_dirs:
            if not driver_dir.exists():
                driver_dir.mkdir(parents=True, exist_ok=True)
                (driver_dir / "__init__.py").touch()

            potential_files = list(driver_dir.glob("*.py")) + list(
                driver_dir.glob("*/__init__.py")
            )

            for py_file in potential_files:
                if py_file.name == "__init__.py" and py_file.parent == driver_dir:
                    continue

                result = self._import_driver_module(py_file)
                if result is None:
                    continue

                module, driver_cls = result

                meta: PluginMeta | None = getattr(module, "METADATA", None)
                if not meta:
                    continue

                score = evaluate_compatible(meta.get("compatible"), compat_ctx)
                if not isinstance(score, ConfidenceScore):
                    score = ConfidenceScore.INCOMPATIBLE

                candidate = DriverCandidate(driver_cls, score, py_file, meta)
                self.all_candidates.append(candidate)

                if score > best_score:
                    best_score = score
                    best_cls = driver_cls
                    best_module = module

        if best_cls and best_module:
            self.active_driver = best_cls()
            for c in self.all_candidates:
                if c.cls is best_cls:
                    c.loaded = True

        # 2. Load Lua Scripts
        script_dir = self.root_dir / "scripts"
        if script_dir.exists() and compat_ctx is not None and config is not None:
            for lua_file in script_dir.glob("*.lua"):
                try:
                    script = LuaScriptWrapper.create_if_compatible(
                        lua_file, compat_ctx, config
                    )
                    if script is not None:
                        script.bind_driver(self.active_driver)
                        self.active_scripts.append(script)
                except Exception as e:
                    print(f"Error loading script {lua_file.name}: {e}")

    def _import_driver_module(
        self, file_path: Path
    ) -> Optional[tuple[Any, type[BaseDriver]]]:
        if file_path.name == "__init__.py":
            module_name = f"dynamic_driver_{file_path.parent.name}"
        else:
            module_name = f"dynamic_driver_{file_path.stem}"

        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            return None

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        driver_cls = getattr(module, "DRIVER", None)
        if driver_cls is None or not issubclass(driver_cls, BaseDriver):
            return None

        return (module, driver_cls)
