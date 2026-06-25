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


def _to_script_data(val: object) -> object:
    """Convert a TickSnapshot field value to a script-compatible dict/list/None."""
    from backend.interfaces.sentinels import Unavailable

    if isinstance(val, Unavailable):
        return None
    if hasattr(val, "model_dump"):
        return val.model_dump()  # type: ignore[return-value]
    if isinstance(val, list):
        result: list[object] = []
        for item in val:
            if hasattr(item, "model_dump"):
                result.append(item.model_dump())  # type: ignore[union-attr]
            else:
                result.append(item)
        return result
    return val


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


def _build_event_dispatch(snapshot: "TickSnapshot") -> dict[str, object]:
    """Build event->data mapping for script dispatch from a TickSnapshot."""
    return {
        "events.general.on_tick": snapshot,
        "events.cpu.on_tick": _to_script_data(snapshot.cpu),
        "events.memory.on_tick": _to_script_data(snapshot.memory),
        "events.disk.on_tick": _to_script_data(snapshot.disk),
        "events.net.on_tick": _to_script_data(snapshot.network),
        "events.process.on_tick": _to_script_data(snapshot.processes),
        "events.gpu.on_tick": _to_script_data(snapshot.gpu),
        "events.battery.on_tick": _to_script_data(snapshot.battery),
        "events.sensor.on_tick": _to_script_data(snapshot.sensors),
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

        if self.db:
            metrics = _snapshot_to_metrics(snapshot)
            self.db.write_snapshot(metrics)

        event_data = _build_event_dispatch(snapshot)
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
