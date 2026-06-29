from __future__ import annotations

from typing import TYPE_CHECKING

from backend.core.loader import DiscoveryLoader
from backend.interfaces.contexts import DriverContext
from backend.interfaces.rules import build_compat_context
from backend.storage.config import ArgusConfig
from backend.storage.database import DatabaseManager

if TYPE_CHECKING:
    from backend.interfaces.contexts import ScriptContext
    from backend.interfaces.sentinels import TickSnapshot, Unavailable
    from backend.interfaces.caps import (
        BatteryMetric, CPUMetric, GPUMetric, MemoryMetric,
        MetricsCollection, NetworkMetric, ProcessMetric,
        SensorMetric, StorageMetric, SystemMetrics,
    )

# A full-TickSnapshot with every field set to Unavailable("error", message)
# used when no driver is loaded.
_ERROR_SNAPSHOT: "TickSnapshot | None" = None


def _error_snapshot(msg: str = "No driver loaded") -> "TickSnapshot":
    """Lazily build an error snapshot so we don't import at module level."""
    global _ERROR_SNAPSHOT
    if _ERROR_SNAPSHOT is None:
        from backend.interfaces.sentinels import TickSnapshot, Unavailable

        u = Unavailable("error", msg)
        _ERROR_SNAPSHOT = TickSnapshot(
            cpu=u, memory=u, processes=u, disk=u, network=u,
            gpu=u, sensors=u, battery=u,
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
    from backend.interfaces.sentinels import Unavailable

    if isinstance(val, Unavailable):
        return None

    from backend.interfaces.caps import MetricsCollection

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

        # List-type subsystems: disk, network, processes, sensors, gpu
        return [m.model_dump() for m in val.metrics]

    # Legacy passthrough for non-MetricsCollection objects
    if hasattr(val, "model_dump"):
        return val.model_dump()  # type: ignore[return-value]
    if isinstance(val, list):
        return [item.model_dump() if hasattr(item, "model_dump") else item for item in val]
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
        "extra": {},
    }


def _snapshot_to_metrics(snapshot: "TickSnapshot") -> "SystemMetrics":
    """Convert TickSnapshot -> SystemMetrics (Unavailable -> None) for DB."""
    from backend.interfaces.caps import (
        BatteryMetric, CPUMetric, GPUMetric, MemoryMetric,
        MetricsCollection, NetworkMetric, ProcessMetric,
        SensorMetric, StorageMetric, SystemMetrics,
    )
    from backend.interfaces.sentinels import Unavailable

    cpu_val: MetricsCollection[CPUMetric] | None = None if isinstance(snapshot.cpu, Unavailable) else snapshot.cpu
    mem_val: MetricsCollection[MemoryMetric] | None = None if isinstance(snapshot.memory, Unavailable) else snapshot.memory
    procs_val: MetricsCollection[ProcessMetric] | None = None if isinstance(snapshot.processes, Unavailable) else snapshot.processes
    disk_val: MetricsCollection[StorageMetric] | None = None if isinstance(snapshot.disk, Unavailable) else snapshot.disk
    net_val: MetricsCollection[NetworkMetric] | None = None if isinstance(snapshot.network, Unavailable) else snapshot.network
    gpu_val: MetricsCollection[GPUMetric] | None = None if isinstance(snapshot.gpu, Unavailable) else snapshot.gpu
    sens_val: MetricsCollection[SensorMetric] | None = None if isinstance(snapshot.sensors, Unavailable) else snapshot.sensors
    bat_val: MetricsCollection[BatteryMetric] | None = None if isinstance(snapshot.battery, Unavailable) else snapshot.battery

    return SystemMetrics(
        cpu=cpu_val or MetricsCollection[CPUMetric](),
        ram=mem_val or MetricsCollection[MemoryMetric](),
        processes=procs_val or MetricsCollection[ProcessMetric](),
        storage=disk_val or MetricsCollection[StorageMetric](),
        network=net_val,
        gpu=gpu_val,
        sensors=sens_val,
        battery=bat_val,
    )


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
    }


class BackendEngine:
    def __init__(self, db: DatabaseManager | None = None) -> None:
        self.config = ArgusConfig()
        self.db = db
        self.compat_ctx = build_compat_context()
        self.loader = DiscoveryLoader()
        self._ctx: "ScriptContext[None] | None" = None
        self.loader.soft_reload(compat_ctx=self.compat_ctx, config=self.config)
        self._init_active_plugins()

    def _init_active_plugins(self) -> None:
        from backend.interfaces.contexts import ScriptContext

        self._ctx = ScriptContext[None](
            data=None,
            config=self.config,
            db=self.db,
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
        """Full engine tick: fetch data, dispatch events, write DB.

        Returns :class:`TickSnapshot` with per-subsystem results.
        """
        if not self.loader.active_driver:
            return _error_snapshot("No driver loaded.")

        drv_ctx = DriverContext(engine=self)
        snapshot: "TickSnapshot" = self.loader.active_driver.tick(drv_ctx)

        # Fetch static system info for CPU core counts and other static fields
        static_info: dict[str, object] | None = None
        if hasattr(self.loader.active_driver, "get_static_info"):
            try:
                si = self.loader.active_driver.get_static_info()
                if si is not None:
                    static_info = si.model_dump()
            except Exception:
                pass

        if self.db:
            metrics = _snapshot_to_metrics(snapshot)
            self.db.write_snapshot(metrics)

        event_data = _build_event_dispatch(snapshot, static_info)
        for script in self.loader.active_scripts:
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
                        print(f"Script Error [{name}][{event_path}]: {e}")

            if hasattr(script, "pop_output"):
                for line in script.pop_output():
                    name = getattr(script.METADATA, "get", lambda *_: "?")(  # type: ignore[union-attr]
                        "name", "?"
                    )
                    print(f"[{name}] {line}")

        return snapshot

    # -- Per-subsystem tick methods ------------------------------------------

    def tick_cpu(self) -> "MetricsCollection[CPUMetric] | Unavailable":
        if not self.loader.active_driver:
            from backend.interfaces.sentinels import Unavailable
            return Unavailable("error", "No driver loaded")
        return self.loader.active_driver.tick_cpu(DriverContext(engine=self))

    def tick_memory(self) -> "MetricsCollection[MemoryMetric] | Unavailable":
        if not self.loader.active_driver:
            from backend.interfaces.sentinels import Unavailable
            return Unavailable("error", "No driver loaded")
        return self.loader.active_driver.tick_memory(DriverContext(engine=self))

    def tick_disk(self) -> "MetricsCollection[StorageMetric] | Unavailable":
        if not self.loader.active_driver:
            from backend.interfaces.sentinels import Unavailable
            return Unavailable("error", "No driver loaded")
        return self.loader.active_driver.tick_disk(DriverContext(engine=self))

    def tick_network(self) -> "MetricsCollection[NetworkMetric] | Unavailable":
        if not self.loader.active_driver:
            from backend.interfaces.sentinels import Unavailable
            return Unavailable("error", "No driver loaded")
        return self.loader.active_driver.tick_network(DriverContext(engine=self))

    def tick_processes(self) -> "MetricsCollection[ProcessMetric] | Unavailable":
        if not self.loader.active_driver:
            from backend.interfaces.sentinels import Unavailable
            return Unavailable("error", "No driver loaded")
        return self.loader.active_driver.tick_processes(DriverContext(engine=self))

    def tick_gpu(self) -> "MetricsCollection[GPUMetric] | Unavailable":
        if not self.loader.active_driver:
            from backend.interfaces.sentinels import Unavailable
            return Unavailable("error", "No driver loaded")
        return self.loader.active_driver.tick_gpu(DriverContext(engine=self))

    def tick_sensors(self) -> "MetricsCollection[SensorMetric] | Unavailable":
        if not self.loader.active_driver:
            from backend.interfaces.sentinels import Unavailable
            return Unavailable("error", "No driver loaded")
        return self.loader.active_driver.tick_sensors(DriverContext(engine=self))

    def tick_battery(self) -> "MetricsCollection[BatteryMetric] | Unavailable":
        if not self.loader.active_driver:
            from backend.interfaces.sentinels import Unavailable
            return Unavailable("error", "No driver loaded")
        return self.loader.active_driver.tick_battery(DriverContext(engine=self))

    # -- Backward compat ----------------------------------------------------

    def get_system_state(self) -> dict[str, object]:
        """Legacy wrapper -- calls :meth:`tick` and converts to dict.

        .. deprecated:: 2.0
            Use :meth:`tick` instead to get a typed :class:`TickSnapshot`.
        """
        snapshot = self.tick()
        from backend.interfaces.sentinels import Unavailable

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
        }

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
