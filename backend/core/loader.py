"""
Discovery Loader for resolving Python Drivers and Lua Scripts.
"""

import ast
import importlib.util
import sys
from pathlib import Path
from typing import Any

from backend.core.python_script import PythonScriptWrapper
from backend.core.sandbox import LuaScriptWrapper
from backend.interfaces.enums import CompatAction, ConfidenceScore
from backend.interfaces.plugins import BaseDriver, PluginMeta
from backend.interfaces.rules import evaluate_compatible, evaluate_script_compatible


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
        self.active_driver: BaseDriver | None = None
        self.active_scripts: list[Any] = []
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
            if mod.startswith("dynamic_driver_") or mod.startswith("dynamic_script_"):
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
            if self.active_driver is not None and getattr(self.active_driver, "_initialized", False):
                self.active_driver.dispose()
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

        # 3. Load Python Scripts
        if script_dir.exists() and compat_ctx is not None and config is not None:
            for py_file in script_dir.glob("*.py"):
                if py_file.name == "__init__.py":
                    continue
                meta = _extract_python_metadata(py_file)
                if meta is None:
                    continue
                compatible_rules = meta.get("compatible")
                result = evaluate_script_compatible(compatible_rules, compat_ctx)  # type: ignore[arg-type]
                if result is not None and not result:
                    continue
                if result is None and config.script_compatibility_default != CompatAction.LOAD:
                    continue
                wrapper = PythonScriptWrapper(py_file, meta)
                wrapper.bind_driver(self.active_driver)
                self.active_scripts.append(wrapper)

    def _import_driver_module(
        self, file_path: Path
    ) -> tuple[Any, type[BaseDriver]] | None:
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

# ------------------------------------------------------------------
# AST-based METADATA extraction for Python scripts (no execution)
# ------------------------------------------------------------------


def _extract_python_metadata(file_path: Path) -> PluginMeta | None:
    """Extract METADATA dict from a Python script using AST (no execution)."""
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
    except SyntaxError:
        return None

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "METADATA":
                    if isinstance(node.value, ast.Dict):
                        return _ast_dict_to_pluginmeta(node.value)
    return None


def _ast_dict_to_pluginmeta(dict_node: ast.Dict) -> PluginMeta:
    from backend.interfaces.enums import Permission

    result: PluginMeta = {
        "name": "Unknown",
        "author": "Unknown",
        "version": "1.0",
        "permissions": [],
    }

    def _flatten_attr(node: ast.Attribute) -> str | None:
        """Flatten ``Permission.X.Y.Z`` to ``\"X.Y.Z\"`` (strip leading ``Permission``)."""
        parts: list[str] = []
        current: ast.AST = node
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        else:
            return None
        parts.reverse()
        if parts and parts[0] == "Permission":
            parts.pop(0)
        if not parts:
            return None
        return ".".join(parts)

    for key, val in zip(dict_node.keys, dict_node.values):
        if not isinstance(key, ast.Constant):
            continue
        k = str(key.value)
        if k == "name" and isinstance(val, ast.Constant):
            result["name"] = str(val.value)
        elif k == "author" and isinstance(val, ast.Constant):
            result["author"] = str(val.value)
        elif k == "version" and isinstance(val, ast.Constant):
            result["version"] = str(val.value)
        elif k == "permissions" and isinstance(val, ast.List):
            perms = []
            for elt in val.elts:
                if isinstance(elt, ast.Attribute):
                    name = _flatten_attr(elt)
                    if name is not None:
                        try:
                            perms.append(Permission(name))
                        except ValueError:
                            pass
                elif isinstance(elt, ast.Constant):
                    try:
                        perms.append(Permission(str(elt.value)))
                    except ValueError:
                        pass
            result["permissions"] = perms
        elif k == "compatible" and isinstance(val, ast.List):
            rules = []
            for elt in val.elts:
                if isinstance(elt, ast.Constant):
                    rules.append(str(elt.value))
            if rules:
                result["compatible"] = rules
    return result
