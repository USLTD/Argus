from __future__ import annotations

import asyncio
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, TypedDict

from pydantic import TypeAdapter, ValidationError

from backend.core.loader import DiscoveryLoader
from backend.interfaces.contexts import DriverContext
from backend.interfaces.enums import ScriptExecutionMode
from backend.interfaces.rules import build_compat_context
from backend.storage.config import ArgusConfig

if TYPE_CHECKING:
    from concurrent.futures import Future
    from backend.interfaces.contexts import ScriptContext
    from backend.interfaces.sentinels import TickSnapshot, Unavailable
    from backend.interfaces.caps import (
        BatteryMetric,
        CPUMetric,
        GPUMetric,
        MemoryMetric,
        MetricsCollection,
        NetworkMetric,
        ProcessMetric,
        SensorMetric,
        StorageMetric,
        SystemCapabilities,
        SystemMetrics,
        UserMetric,
    )
    from backend.interfaces.enums import (
        ConfidenceScore,
        Permission,
    )
    from backend.interfaces.plugins import BaseUserScript

import datetime
from backend.core.python_script import PythonScriptWrapper
from backend.core.sandbox import LuaScriptWrapper

from backend.interfaces.caps import MetricsCollection
from backend.interfaces.contexts import ScriptContext
from backend.interfaces.sentinels import TickSnapshot, Unavailable


class ScriptInfo(TypedDict):
    """Metadata for a loaded user script."""

    name: str
    path: str
    type: str  # "lua" or "python"
    execution_mode: ScriptExecutionMode
    permissions: list[Permission]
    hooked_events: list[str]


class DriverInfo(TypedDict):
    """Metadata for a discovered driver candidate."""

    name: str
    path: str
    score: ConfidenceScore
    capabilities: SystemCapabilities | None


class DriverStatus(TypedDict):
    """Detailed status for a discovered driver candidate."""

    name: str
    class_name: str
    is_active: bool
    score: ConfidenceScore
    capabilities: SystemCapabilities | None
    compatible_platforms: list[str]
    file_path: str


class ScriptStatus(TypedDict):
    """Detailed status for a loaded user script."""

    name: str
    path: str
    type: str  # "lua" or "python"
    execution_mode: ScriptExecutionMode
    permissions: list[Permission]
    hooked_events: list[str]
    line_count: int


# A full-TickSnapshot with every field set to Unavailable("error", message)
# used when no driver is loaded.
_ERROR_SNAPSHOT: "TickSnapshot | None" = None


def _error_snapshot(msg: str = "No driver loaded") -> "TickSnapshot":
    """Lazily build an error snapshot so we don't import at module level."""
    global _ERROR_SNAPSHOT
    if _ERROR_SNAPSHOT is None:
        u = Unavailable("error", msg)
        _ERROR_SNAPSHOT = TickSnapshot(
            cpu=u,
            memory=u,
            processes=u,
            disk=u,
            network=u,
            gpu=u,
            sensors=u,
            battery=u,
            users=u,
        )
    return _ERROR_SNAPSHOT


def _to_script_data(
    val: object,
    subsystem: str | None = None,
    static_info: dict[str, object] | None = None,
) -> object:
    """Convert a TickSnapshot field to a flat TickData-shaped dict for scripts.

    * ``Unavailable`` → ``None``
    * ``MetricsCollection[T]`` → flat TickData dict (scalar for battery/memory/cpu,
      list of dicts for disk/network/processes/sensors/gpu)
    * Other model-dumpable objects → ``model_dump()``
    * Lists → list of ``model_dump()``
    * Everything else → identity
    """
    if isinstance(val, Unavailable):
        return None

    if isinstance(val, MetricsCollection):
        if not val.metrics:
            # Empty collection: scalar subsystems return None, list ones return []
            return None if subsystem in ("battery", "memory", "cpu") else []

        if subsystem == "battery":
            return val.metrics[0].model_dump()
        if subsystem == "memory":
            return val.metrics[0].model_dump()
        if subsystem == "cpu":
            aggregate = None
            per_core: list[float] = []
            for m in val.metrics:
                if m.core_id is None:
                    aggregate = m
                else:
                    per_core.append(m.usage_percent)

            if aggregate is None and val.metrics:
                aggregate = val.metrics[0]

            if aggregate is None:
                return None

            result = aggregate.model_dump()
            result["per_core"] = per_core
            result.pop("core_id", None)

            phys: int = 0
            logi: int = 0
            if static_info:
                phys = static_info.get("cpu_physical_cores", 0) or 0  # type: ignore[assignment]
                logi = static_info.get("cpu_logical_cores", 0) or 0  # type: ignore[assignment]

            result["physical_cores"] = phys
            result["logical_cores"] = logi
            return result

        # List-type subsystems: disk, network, processes, sensors, gpu, users
        return [m.model_dump() for m in val.metrics]

    # Legacy passthrough for non-MetricsCollection objects
    if hasattr(val, "model_dump"):
        return val.model_dump()  # type: ignore[return-value]
    if isinstance(val, list):
        return [
            item.model_dump() if hasattr(item, "model_dump") else item for item in val
        ]
    return val


def _snapshot_to_general_dict(
    snapshot: "TickSnapshot",
    static_info: dict[str, object] | None = None,
) -> dict[str, object]:
    """Convert TickSnapshot to a flat dict matching the ``GeneralTickData`` shape."""
    return {
        "cpu": _to_script_data(snapshot.cpu, "cpu", static_info),
        "ram": _to_script_data(snapshot.memory, "memory"),
        "processes": _to_script_data(snapshot.processes, "processes"),
        "storage": _to_script_data(snapshot.disk, "disk"),
        "gpu": _to_script_data(snapshot.gpu, "gpu"),
        "network": _to_script_data(snapshot.network, "network"),
        "sensors": _to_script_data(snapshot.sensors, "sensors"),
        "battery": _to_script_data(snapshot.battery, "battery"),
        "users": _to_script_data(snapshot.users, "users"),
        "extra": {},
    }


def _build_event_dispatch(
    snapshot: "TickSnapshot",
    static_info: dict[str, object] | None = None,
) -> dict[str, object]:
    """Build event->data mapping for script dispatch from a TickSnapshot.

    The ``events.general.on_tick`` key receives the full ``GeneralTickData``-shaped
    dict.  Each per-subsystem key receives the flat TickData dict (or list) for
    that subsystem alone, so scripts can subscribe to specific events.
    """
    return {
        "events.general.on_tick": _snapshot_to_general_dict(snapshot, static_info),
        "events.cpu.on_tick": _to_script_data(snapshot.cpu, "cpu", static_info),
        "events.memory.on_tick": _to_script_data(snapshot.memory, "memory"),
        "events.disk.on_tick": _to_script_data(snapshot.disk, "disk"),
        "events.net.on_tick": _to_script_data(snapshot.network, "network"),
        "events.process.on_tick": _to_script_data(snapshot.processes, "processes"),
        "events.gpu.on_tick": _to_script_data(snapshot.gpu, "gpu"),
        "events.battery.on_tick": _to_script_data(snapshot.battery, "battery"),
        "events.sensor.on_tick": _to_script_data(snapshot.sensors, "sensors"),
        "events.users.on_tick": _to_script_data(snapshot.users, "users"),
    }


class BackendEngine:
    def __init__(
        self,
        on_tick_callback: Callable[["TickSnapshot"], None] | None = None,
    ) -> None:
        self.config = ArgusConfig()
        self.compat_ctx = build_compat_context()
        self.loader = DiscoveryLoader()
        self._ctx: "ScriptContext[None] | None" = None
        self._on_tick_callback = on_tick_callback
        self.loader.soft_reload(compat_ctx=self.compat_ctx, config=self.config)
        self._init_active_plugins()
        self._last_tick_duration: float = 0.0
        self._last_tick_times: dict[str, float] = {}
        self._process_tick_counter: int = 0
        self._last_process_snapshot: (
            MetricsCollection[ProcessMetric] | Unavailable | None
        ) = None
        self._executor = ThreadPoolExecutor(max_workers=self.config.script_batch_size)
        self._futures: list[Future] = []
        self._lock = threading.Lock()
        self._config_changed = asyncio.Event()

    @property
    def last_tick_duration(self) -> float:
        """Duration of the last :meth:`tick` call in seconds."""
        return self._last_tick_duration

    @property
    def config_changed(self) -> asyncio.Event:
        """An asyncio.Event that is set whenever config changes.

        Screens in the TUI can ``await engine.config_changed.wait()``
        in their polling loops to detect and react to config changes.
        The event is automatically cleared after each read.
        """
        return self._config_changed

    def _init_active_plugins(self) -> None:
        self._ctx = ScriptContext[None](
            data=None,
            config=self.config,
            driver=self.loader.active_driver,
        )
        for script in self.loader.active_scripts:
            if hasattr(script, "trigger_load"):
                try:
                    script.trigger_load(self._ctx)
                except Exception as e:
                    name = getattr(script.METADATA, "get", lambda *_: "?")(  # type: ignore[union-attr]
                        "name", "?"
                    )
                    print(f"Hook error [{name}]: {e}")

    # -- Aggregate tick ------------------------------------------------------

    def tick(self) -> "TickSnapshot":
        """Full engine tick: fetch data, dispatch events.

        Returns :class:`TickSnapshot` with per-subsystem results.
        """
        if not self.loader.active_driver:
            return _error_snapshot("No driver loaded.")

        _tick_start = time.monotonic()
        drv_ctx = DriverContext(engine=self)
        snapshot: "TickSnapshot" = self.loader.active_driver.tick(drv_ctx)

        # Cache/reuse process data based on tick interval
        if self._process_tick_counter % self.config.process_tick_interval == 0:
            self._last_process_snapshot = snapshot.processes
        elif self._last_process_snapshot is not None:
            snapshot = replace(snapshot, processes=self._last_process_snapshot)

        # Fetch static system info for CPU core counts and other static fields
        static_info: dict[str, object] | None = None
        if hasattr(self.loader.active_driver, "get_static_info"):
            try:
                si = self.loader.active_driver.get_static_info()
                if si is not None:
                    static_info = si.model_dump()
            except Exception:
                pass

        # Early-skip: only build event dispatch when scripts are loaded
        if self.loader.active_scripts:
            event_data = _build_event_dispatch(snapshot, static_info)
            for script in self.loader.active_scripts:
                mode = script.execution_mode  # type: ignore[union-attr]

                if mode == ScriptExecutionMode.BLOCKING:
                    output = self._dispatch_script(script, event_data)
                    for line in output:
                        print(line)

                elif mode == ScriptExecutionMode.NONBLOCKING:
                    future = self._executor.submit(
                        self._dispatch_script, script, event_data
                    )
                    with self._lock:
                        self._futures.append(future)

                elif mode == ScriptExecutionMode.MIXED:
                    future = self._executor.submit(
                        self._dispatch_script, script, event_data
                    )
                    try:
                        output = future.result(
                            timeout=self.config.script_timeout_ms / 1000
                        )
                        for line in output:
                            print(line)
                    except TimeoutError:
                        with self._lock:
                            self._futures.append(future)

        self._collect_pending_output()

        if self._on_tick_callback:
            self._on_tick_callback(snapshot)

        self._process_tick_counter += 1
        self._last_tick_duration = time.monotonic() - _tick_start
        return snapshot

    # -- Script dispatch helpers ---------------------------------------------

    def _dispatch_script(
        self,
        script: BaseUserScript,
        event_data: dict[str, object],
    ) -> list[str]:
        output_lines: list[str] = []
        for event_path, data in event_data.items():
            if data is not None:
                try:
                    if hasattr(script, "dispatch"):
                        script.dispatch(event_path, data)
                    else:
                        exec_tick = getattr(script, "execute_tick", None)
                        if exec_tick:
                            exec_tick(data)
                except Exception as e:
                    name = getattr(script.METADATA, "get", lambda *_: "?")(  # type: ignore[union-attr]
                        "name", "?"
                    )
                    output_lines.append(f"Script Error [{name}][{event_path}]: {e}")

        if hasattr(script, "pop_output"):
            for line in script.pop_output():  # type: ignore[union-attr]
                name = getattr(script.METADATA, "get", lambda *_: "?")(  # type: ignore[union-attr]
                    "name", "?"
                )
                output_lines.append(f"[{name}] {line}")
        return output_lines

    def _collect_pending_output(self) -> None:
        with self._lock:
            completed: list[Future] = [f for f in self._futures if f.done()]
            for future in completed:
                try:
                    for line in future.result(timeout=0):
                        print(line)
                except Exception:
                    pass
                self._futures.remove(future)

    def shutdown(self) -> None:
        """Gracefully shut down the thread-pool executor.

        Cancel pending futures and wait for running tasks to finish.
        """
        with self._lock:
            for future in self._futures:
                future.cancel()
            self._futures.clear()
        self._executor.shutdown(wait=True)

    # -- Per-subsystem tick methods ------------------------------------------

    def tick_cpu(self) -> "MetricsCollection[CPUMetric] | Unavailable":
        if not self.loader.active_driver:
            return Unavailable("error", "No driver loaded")
        _t0 = time.monotonic()
        result = self.loader.active_driver.tick_cpu(DriverContext(engine=self))
        self._last_tick_times["cpu"] = time.monotonic() - _t0
        return result

    def tick_memory(self) -> "MetricsCollection[MemoryMetric] | Unavailable":
        if not self.loader.active_driver:
            return Unavailable("error", "No driver loaded")
        _t0 = time.monotonic()
        result = self.loader.active_driver.tick_memory(DriverContext(engine=self))
        self._last_tick_times["memory"] = time.monotonic() - _t0
        return result

    def tick_disk(self) -> "MetricsCollection[StorageMetric] | Unavailable":
        if not self.loader.active_driver:
            return Unavailable("error", "No driver loaded")
        _t0 = time.monotonic()
        result = self.loader.active_driver.tick_disk(DriverContext(engine=self))
        self._last_tick_times["disk"] = time.monotonic() - _t0
        return result

    def tick_network(self) -> "MetricsCollection[NetworkMetric] | Unavailable":
        if not self.loader.active_driver:
            return Unavailable("error", "No driver loaded")
        _t0 = time.monotonic()
        result = self.loader.active_driver.tick_network(DriverContext(engine=self))
        self._last_tick_times["network"] = time.monotonic() - _t0
        return result

    def tick_processes(self) -> "MetricsCollection[ProcessMetric] | Unavailable":
        if not self.loader.active_driver:
            return Unavailable("error", "No driver loaded")
        _t0 = time.monotonic()
        result = self.loader.active_driver.tick_processes(DriverContext(engine=self))
        self._last_tick_times["processes"] = time.monotonic() - _t0
        return result

    def tick_gpu(self) -> "MetricsCollection[GPUMetric] | Unavailable":
        if not self.loader.active_driver:
            return Unavailable("error", "No driver loaded")
        _t0 = time.monotonic()
        result = self.loader.active_driver.tick_gpu(DriverContext(engine=self))
        self._last_tick_times["gpu"] = time.monotonic() - _t0
        return result

    def tick_sensors(self) -> "MetricsCollection[SensorMetric] | Unavailable":
        if not self.loader.active_driver:
            return Unavailable("error", "No driver loaded")
        _t0 = time.monotonic()
        result = self.loader.active_driver.tick_sensors(DriverContext(engine=self))
        self._last_tick_times["sensors"] = time.monotonic() - _t0
        return result

    def tick_battery(self) -> "MetricsCollection[BatteryMetric] | Unavailable":
        if not self.loader.active_driver:
            return Unavailable("error", "No driver loaded")
        _t0 = time.monotonic()
        result = self.loader.active_driver.tick_battery(DriverContext(engine=self))
        self._last_tick_times["battery"] = time.monotonic() - _t0
        return result

    def tick_users(self) -> "MetricsCollection[UserMetric] | Unavailable":
        if not self.loader.active_driver:
            return Unavailable("error", "No driver loaded")
        _t0 = time.monotonic()
        result = self.loader.active_driver.tick_users(DriverContext(engine=self))  # type: ignore[attr-defined]  # basedpyright false positive: BaseDriver.tick_users exists at runtime
        self._last_tick_times["users"] = time.monotonic() - _t0
        return result

    # -- Selective tick -----------------------------------------------------

    def tick_subsystem(self, name: str) -> "MetricsCollection | Unavailable":
        """Tick a single subsystem by name.

        Args:
            name: Subsystem name (e.g. ``"cpu"``, ``"memory"``, ``"disk"``).

        Returns:
            ``MetricsCollection[T]`` for the subsystem, or ``Unavailable``
            if the driver is not loaded, the method is missing, or an error
            occurs.
        """
        if not self.loader.active_driver:
            return Unavailable("error", "No driver loaded")

        method = getattr(self.loader.active_driver, f"tick_{name}", None)
        if method is None:
            return Unavailable("unsupported", f"Driver has no tick_{name} method")

        _t0 = time.monotonic()
        result = method(DriverContext(engine=self))
        self._last_tick_times[name] = time.monotonic() - _t0
        return result

    def tick_selective(self, subsystems: set[str]) -> dict[str, object]:
        """Tick a selected set of subsystems, respecting config enable/disable.

        Each subsystem is collected independently; a failure in one does
        not prevent the others from being collected.

        Args:
            subsystems: Set of subsystem names (e.g. ``{"cpu", "memory"}``).

        Returns:
            Dict mapping each subsystem name to its ``MetricsCollection``
            or ``Unavailable`` value.
        """
        _t0 = time.monotonic()
        result: dict[str, object] = {}
        for name in subsystems:
            enabled = self.config.subsystem_enabled.get(name, True)
            if not enabled:
                result[name] = Unavailable(
                    "disabled", f"Subsystem '{name}' is disabled in config"
                )
                continue
            try:
                result[name] = self.tick_subsystem(name)
            except Exception as e:
                result[name] = Unavailable("error", str(e))
        self._last_tick_times["total"] = time.monotonic() - _t0
        return result

    def get_tick_times(self) -> dict[str, float]:
        """Return per-subsystem tick timing data.

        Returns:
            A copy of the timing dict mapping subsystem names to their
            last tick duration in seconds. The ``"total"`` key contains
            the total time of the last :meth:`tick_selective` call.
        """
        return dict(self._last_tick_times)

    # -- Backward compat ----------------------------------------------------

    def get_system_state(self) -> dict[str, object]:
        """Legacy wrapper -- calls :meth:`tick` and converts to dict.

        .. deprecated:: 2.0
            Use :meth:`tick` instead to get a typed :class:`TickSnapshot`.
        """
        snapshot = self.tick()

        def _to_dict(val: object) -> object:
            if isinstance(val, Unavailable):
                return None
            if hasattr(val, "model_dump"):
                return val.model_dump()  # type: ignore[return-value]
            if isinstance(val, list):
                return [
                    item.model_dump() if hasattr(item, "model_dump") else item  # type: ignore[union-attr]
                    for item in val
                ]
            if hasattr(val, "__dataclass_fields__"):
                return {f: _to_dict(getattr(val, f)) for f in val.__dataclass_fields__}  # type: ignore[union-attr]
            return val

        return {
            "cpu": _to_dict(snapshot.cpu),
            "ram": _to_dict(snapshot.memory),
            "processes": _to_dict(snapshot.processes),
            "storage": _to_dict(snapshot.disk),
            "network": _to_dict(snapshot.network),
            "gpu": _to_dict(snapshot.gpu),
            "sensors": _to_dict(snapshot.sensors),
            "battery": _to_dict(snapshot.battery),
            "users": _to_dict(snapshot.users),
        }

    # -- Script management API ------------------------------------------------

    def list_scripts(self) -> list[ScriptInfo]:
        """Return metadata for all loaded scripts."""

        result: list[ScriptInfo] = []
        for script in self.loader.active_scripts:
            meta = script.METADATA or {}
            script_type: str = (
                "lua" if isinstance(script, LuaScriptWrapper) else "python"
            )
            result.append(
                {
                    "name": str(meta.get("name", "?")),
                    "path": str(script.file_path) if script.file_path else "",
                    "type": script_type,
                    "execution_mode": script.execution_mode,  # type: ignore[reportAttributeAccessIssue]  # basedpyright false positive: BaseUserScript.execution_mode exists at runtime
                    "permissions": list(meta.get("permissions", [])),
                    "hooked_events": [],
                }
            )
        return result

    def get_script_source(self, name: str) -> str:
        """Return the full source code of a loaded script by name."""
        for script in self.loader.active_scripts:
            meta = script.METADATA or {}
            if meta.get("name") == name:
                if script.file_path:
                    return script.file_path.read_text(encoding="utf-8")
                raise ValueError(f"Script '{name}' has no file path")
        msg = f"Script '{name}' not found"
        raise ValueError(msg)

    def reload_script(self, name: str) -> bool:
        """Reload a script by name.

        Unloads the script and triggers a full soft_reload.
        Returns True on success, False on failure.
        """
        found = False
        for script in self.loader.active_scripts:
            meta = script.METADATA or {}
            if meta.get("name") == name:
                found = True
                if hasattr(script, "trigger_unload") and self._ctx:
                    try:
                        script.trigger_unload(self._ctx)
                    except Exception:
                        pass
                break

        if not found:
            msg = f"Script '{name}' not found"
            raise ValueError(msg)

        try:
            self.loader.soft_reload(compat_ctx=self.compat_ctx, config=self.config)
            self._init_active_plugins()
            return True
        except Exception:
            return False

    def unload_script(self, name: str) -> bool:
        """Unload a script by name, removing it from active scripts."""
        for i, script in enumerate(self.loader.active_scripts):
            meta = script.METADATA or {}
            if meta.get("name") == name:
                if hasattr(script, "trigger_unload") and self._ctx:
                    try:
                        script.trigger_unload(self._ctx)
                    except Exception:
                        pass
                self.loader.active_scripts.pop(i)
                return True
        msg = f"Script '{name}' not found"
        raise ValueError(msg)

    def get_script_status(self, name: str) -> ScriptStatus:
        """Return detailed status for a loaded script by name."""

        for script in self.loader.active_scripts:
            meta = script.METADATA or {}
            if meta.get("name") == name:
                script_type: str = (
                    "lua" if isinstance(script, LuaScriptWrapper) else "python"
                )

                hooked_events: list[str] = list(getattr(script, "hooks", []) or [])
                if not hooked_events:
                    handlers = getattr(script, "_event_handlers", None)
                    if handlers is not None:
                        hooked_events = list(handlers.keys())

                line_count = 0
                if script.file_path:
                    try:
                        line_count = len(
                            script.file_path.read_text(encoding="utf-8").splitlines()
                        )
                    except Exception:
                        pass

                return {
                    "name": str(meta.get("name", "?")),
                    "path": str(script.file_path) if script.file_path else "",
                    "type": script_type,
                    "execution_mode": script.execution_mode,  # type: ignore[reportAttributeAccessIssue]  # basedpyright false positive: BaseUserScript.execution_mode exists at runtime
                    "permissions": list(meta.get("permissions", [])),
                    "hooked_events": hooked_events,
                    "line_count": line_count,
                }
        msg = f"Script '{name}' not found"
        raise ValueError(msg)

    def list_drivers(self) -> list[DriverInfo]:
        """Return metadata for all discovered driver candidates."""
        result: list[DriverInfo] = []
        for candidate in self.loader.all_candidates:
            capabilities: SystemCapabilities | None = None
            if candidate.loaded and self.loader.active_driver is not None:
                try:
                    caps = self.loader.active_driver.get_capabilities()
                    if caps is not None:
                        capabilities = caps
                except Exception:
                    pass

            result.append(
                {
                    "name": str(candidate.meta.get("name", "?")),
                    "path": str(candidate.file_path),
                    "score": candidate.score,
                    "capabilities": capabilities,
                }
            )
        return result

    def get_driver_status(self, name: str) -> DriverStatus:
        """Return detailed status for a discovered driver candidate by name."""
        for candidate in self.loader.all_candidates:
            if str(candidate.meta.get("name", "?")) == name:
                capabilities: SystemCapabilities | None = None
                if candidate.loaded and self.loader.active_driver is not None:
                    try:
                        caps = self.loader.active_driver.get_capabilities()
                        if caps is not None:
                            capabilities = caps
                    except Exception:
                        pass

                compatible_raw = candidate.meta.get("compatible")
                if isinstance(compatible_raw, list):
                    compatible_platforms = [str(p) for p in compatible_raw]
                else:
                    compatible_platforms = []

                return {
                    "name": str(candidate.meta.get("name", "?")),
                    "class_name": candidate.cls.__name__,
                    "is_active": candidate.loaded,
                    "score": candidate.score,
                    "capabilities": capabilities,
                    "compatible_platforms": compatible_platforms,
                    "file_path": str(candidate.file_path),
                }
        msg = f"Driver '{name}' not found"
        raise ValueError(msg)

    def switch_driver(self, name: str) -> bool:
        """Switch the active driver to a discovered driver candidate by name.

        Returns True if the driver is now active (either switched or already active).
        Raises ValueError if the driver name is not found among candidates.
        """
        for candidate in self.loader.all_candidates:
            if str(candidate.meta.get("name", "?")) == name:
                if candidate.loaded:
                    return True

                if self.loader.active_driver is not None:
                    try:
                        self.loader.active_driver.dispose()
                    except Exception:
                        pass

                self.loader.active_driver = candidate.cls()

                for c in self.loader.all_candidates:
                    c.loaded = c is candidate

                for script in self.loader.active_scripts:
                    if hasattr(script, "bind_driver"):
                        try:
                            script.bind_driver(self.loader.active_driver)
                        except Exception:
                            pass

                return True

        msg = f"Driver '{name}' not found"
        raise ValueError(msg)

    def set_script_execution_mode(
        self, script_name: str, mode: ScriptExecutionMode
    ) -> None:
        """Change a script's execution mode by name."""
        for script in self.loader.active_scripts:
            meta = script.METADATA
            if meta is not None and meta.get("name") == script_name:
                script.execution_mode = mode  # type: ignore[reportAttributeAccessIssue]  # basedpyright false positive: BaseUserScript.execution_mode exists at runtime
                return
        msg = f"Script '{script_name}' not found"
        raise ValueError(msg)

    def set_script_permissions(
        self, script_name: str, permissions: list[Permission]
    ) -> None:
        """Update a script's allowed permissions by name."""
        for script in self.loader.active_scripts:
            meta = script.METADATA
            if meta is not None and meta.get("name") == script_name:
                meta["permissions"] = permissions  # type: ignore[typeddict-item]
                return
        msg = f"Script '{script_name}' not found"
        raise ValueError(msg)

    # -- Runtime config API -------------------------------------------------

    def set_config(self, key: str, value: Any) -> None:
        """Set a runtime config field with validation and side effects.

        Args:
            key: A valid ``ArgusConfig`` field name.
            value: The new value (type-validated against the field annotation).

        Raises:
            ValueError: If *key* is not a valid config field or *value*
                fails pydantic type validation.
        """
        if key not in ArgusConfig.model_fields:
            raise ValueError(f"Unknown config field: {key}")

        field_info = ArgusConfig.model_fields[key]
        if isinstance(value, str) and key == "script_execution_mode":
            try:
                value = ScriptExecutionMode[value.upper()]
            except KeyError:
                raise ValueError(
                    f"Invalid value for '{key}': '{value}'. "
                    f"Expected one of: nonblocking, blocking, mixed"
                )
        ta = TypeAdapter(field_info.annotation)
        try:
            validated = ta.validate_python(value)
        except ValidationError as e:
            raise ValueError(f"Invalid value for '{key}': {e}") from e

        old_executor: ThreadPoolExecutor | None = None
        if key == "script_batch_size":
            old_executor = self._executor

        setattr(self.config, key, validated)
        self.config.save()
        self._config_changed.set()

        if key == "script_batch_size":
            self._executor = ThreadPoolExecutor(max_workers=validated)
            if old_executor is not None:
                old_executor.shutdown(wait=False)
        elif key == "process_tick_interval":
            self._process_tick_counter = 0

    def get_config(self) -> dict[str, Any]:
        """Return the current runtime configuration as a plain dict.

        Returns:
            All ``ArgusConfig`` fields serialised via ``model_dump(mode="json")``.
        """
        return dict(self.config.model_dump(mode="json"))

    # -- Plugin lifecycle ---------------------------------------------------

    def trigger_soft_reload(self) -> None:
        if self._ctx:
            for script in self.loader.active_scripts:
                if hasattr(script, "trigger_unload"):
                    try:
                        script.trigger_unload(self._ctx)
                    except Exception:
                        pass

        self.loader.soft_reload(compat_ctx=self.compat_ctx, config=self.config)
        self._init_active_plugins()
