from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypedDict

from PyQt6.QtCore import QObject, pyqtSignal, QTimer

from backend.interfaces.contexts import BridgeContext

if TYPE_CHECKING:
    from backend.core.engine import BackendEngine, ScriptInfo
    from backend.interfaces.enums import Permission, ScriptExecutionMode
    from backend.storage.config import ArgusConfig

import datetime

from backend.interfaces.caps import UnavailableInfo
from backend.interfaces.caps import dump_static_info as _dump
from backend.interfaces.enums import Permission
from backend.interfaces.permissions import PermissionHierarchy


# ------------------------------------------------------------------
# TypedDicts  —  return-type contracts for every get_*() method
# ------------------------------------------------------------------


class CpuMetricsDict(TypedDict):
    cpu_percent: float
    per_core: list[float]
    frequency: float | None
    physical_cores: int
    logical_cores: int


class MemoryMetricsDict(TypedDict):
    total: int
    used: int
    available: int
    free: int
    cached: int
    percent: float


class DiskUsageDict(TypedDict):
    total: int
    used: int
    free: int
    percent: float


class NetworkIODict(TypedDict):
    bytes_sent: int
    bytes_recv: int


class ProcessEntryDict(TypedDict):
    pid: int
    name: str
    cpu_percent: float
    memory_info: int
    status: str
    num_threads: int
    username: str | None
    ppid: int | None
    create_time: float | None
    exe: str | None


class SensorsDict(TypedDict):
    temperatures: dict[str, list[float]]


class SystemLoadDict(TypedDict):
    cpu_percent: float
    processes: int
    threads: int
    handles: int


class StaticInfoDict(TypedDict, total=False):
    """Static system info with nested sub-model keys."""
    cpu: dict
    gpu: dict
    motherboard: dict
    os: dict
    memory: dict
    system: dict


class BatteryDict(TypedDict):
    percent: float
    power_plugged: bool | None
    seconds_left: float | None


class AggregatedStateDict(TypedDict):
    cpu: CpuMetricsDict
    memory: MemoryMetricsDict
    disks: list[DiskUsageDict]
    network: NetworkIODict
    processes: list[ProcessEntryDict]
    sensors: dict[str, list[float]]
    battery: BatteryDict
    boot_time: float
    load: SystemLoadDict
    static_info: StaticInfoDict


# ------------------------------------------------------------------
# EngineBridge  —  QObject with QTimer and typed public API
# ------------------------------------------------------------------


class EngineBridge(QObject):
    """Wraps BackendEngine and exposes typed dict methods for frontend consumption.

    Emits ``state_updated`` with a ``BridgeContext`` on each timer tick.

    Usage
    -----
    .. code-block:: python

        engine = BackendEngine(...)
        bridge = EngineBridge(engine)
        bridge.state_updated.connect(my_handler)
        bridge.start_polling()

    Callers may also access the individual ``get_*()`` methods directly
    without starting the timer.
    """

    state_updated = pyqtSignal(BridgeContext)
    config_changed_signal = pyqtSignal(dict)

    def __init__(
        self,
        engine: Any = None,
        parent: QObject | None = None,
        permissions: set[Permission] | None = None,
        config: ArgusConfig | None = None,
    ) -> None:
        super().__init__(parent)
        self._engine = engine
        self._permissions = permissions
        self._config = config
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._state_cache: dict[str, Any] | None = None
        self._last_network_io: NetworkIODict | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start_polling(self, interval_ms: int | None = None) -> None:
        """Start the internal tick timer with the configured interval."""
        if interval_ms is None:
            interval_ms = self._config.poll_interval_ms if self._config else 1000
        self._timer.start(interval_ms)

    def set_interval(self, ms: int) -> None:
        """Restart the timer with a new interval (ms)."""
        self._timer.stop()
        self._timer.start(ms)

    def stop_polling(self) -> None:
        """Stop the internal tick timer."""
        self._timer.stop()
        self._state_cache = None

    def _tick(self) -> None:
        """Timer callback: emit ``state_updated`` with a fresh BridgeContext."""
        self._refresh_cache()
        data = self.get_all()
        ctx = BridgeContext(data=data, bridge=self)
        self.state_updated.emit(ctx)

    # ------------------------------------------------------------------
    # Permission check
    # ------------------------------------------------------------------

    def _check(self, required: Permission) -> bool:
        """Check if the bridge's permissions satisfy *required*.

        None = unrestricted (frontend use). Empty set = no data.
        """
        if self._permissions is None:
            return True
        return any(
            PermissionHierarchy.grants(p, required) for p in self._permissions
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @property
    def _state(self) -> dict[str, Any]:
        if self._state_cache is not None:
            return self._state_cache
        if self._engine is None:
            return {}
        try:
            return self._engine.get_system_state()
        except Exception:
            return {}

    def _refresh_cache(self) -> None:
        """Fetch fresh state from engine and populate the per-tick cache."""
        if self._engine is None:
            self._state_cache = {}
            return
        try:
            self._state_cache = self._engine.get_system_state()
        except Exception:
            self._state_cache = {}

    @property
    def _driver(self) -> Any:
        if self._engine is None:
            return None
        return getattr(getattr(self._engine, "loader", None), "active_driver", None)

    # ------------------------------------------------------------------
    # Public API  —  each method returns a TypedDict
    # ------------------------------------------------------------------

    def get_cpu_metrics(self) -> CpuMetricsDict:
        """CPU usage, per-core breakdown, frequency and core counts."""
        if not self._check(Permission.CPU_READ):
            return CpuMetricsDict(cpu_percent=0.0, per_core=[], frequency=None, physical_cores=0, logical_cores=0)
        state = self._state
        cpu = state.get("cpu", {})
        assert isinstance(cpu, dict)
        metrics = cpu.get("metrics", [])
        agg = metrics[0] if metrics else {}

        per_core_data = [
            m["usage_percent"]
            for m in metrics[1:]
            if "usage_percent" in m
        ]

        static = state.get("static_info", {})
        cpu_static = static.get("cpu", {}) if isinstance(static, dict) else {}
        raw_cores = cpu_static.get("physical_cores", 0)
        raw_threads = cpu_static.get("logical_cores", 0)
        return CpuMetricsDict(
            cpu_percent=agg.get("usage_percent", 0.0),
            per_core=per_core_data,
            frequency=agg.get("frequency_mhz"),
            physical_cores=raw_cores if isinstance(raw_cores, int) else 0,
            logical_cores=raw_threads if isinstance(raw_threads, int) else 0,
        )

    def get_memory_metrics(self) -> MemoryMetricsDict:
        """RAM totals, usage, available, free, cached and percent."""
        if not self._check(Permission.MEMORY_READ):
            return MemoryMetricsDict(total=0, used=0, available=0, free=0, cached=0, percent=0.0)
        state = self._state
        ram = state.get("ram", {})
        assert isinstance(ram, dict)
        metrics = ram.get("metrics", [{}])
        m = metrics[0] if metrics else {}
        total = m.get("total_bytes", 0)
        used = m.get("used_bytes", 0)
        available = m.get("available_bytes", 0)
        percent = m.get("percent", 0.0)
        return MemoryMetricsDict(
            total=total,
            used=used,
            available=available,
            free=available,  # engine reports 'available' as free
            cached=0,
            percent=percent,
        )

    def get_disk_usage(self, path: str) -> DiskUsageDict:
        """Usage stats for *path* (total / used / free bytes + percent)."""
        if not self._check(Permission.DISK_READ):
            return DiskUsageDict(total=0, used=0, free=0, percent=0.0)
        state = self._state
        storage_container = state.get("storage", {})
        assert isinstance(storage_container, dict)
        storage_list = storage_container.get("metrics", [])
        for disk in storage_list:
            if isinstance(disk, dict) and disk.get("mount_point", "") == path:
                return DiskUsageDict(
                    total=disk.get("total_bytes", 0),
                    used=disk.get("used_bytes", 0),
                    free=disk.get("free_bytes", 0),
                    percent=disk.get("percent", 0.0),
                )
        return DiskUsageDict(total=0, used=0, free=0, percent=0.0)

    def get_network_io(self) -> NetworkIODict:
        """Network I/O rates (bytes/sec delta)."""
        if not self._check(Permission.NETWORK_READ):
            return NetworkIODict(bytes_sent=0, bytes_recv=0)
        state = self._state
        net_container = state.get("network", {})
        net_list = net_container.get("metrics", []) if isinstance(net_container, dict) else []
        total_sent = 0
        total_recv = 0
        for iface in net_list:
            if isinstance(iface, dict):
                total_sent += iface.get("bytes_sent", 0)
                total_recv += iface.get("bytes_recv", 0)
        current = NetworkIODict(bytes_sent=total_sent, bytes_recv=total_recv)
        if self._last_network_io is not None:
            delta = NetworkIODict(
                bytes_sent=current["bytes_sent"] - self._last_network_io["bytes_sent"],
                bytes_recv=current["bytes_recv"] - self._last_network_io["bytes_recv"],
            )
            self._last_network_io = current
            return delta
        self._last_network_io = current
        return current

    def get_process_list(self) -> list[ProcessEntryDict]:
        """Return the current process list from the engine state."""
        if not self._check(Permission.PROCESSES_READ):
            return []
        state = self._state
        proc_container = state.get("processes", {})
        proc_list: list[dict[str, Any]] = []
        if isinstance(proc_container, dict):
            proc_list = proc_container.get("metrics", [])
        elif isinstance(proc_container, list):
            proc_list = proc_container
        result: list[ProcessEntryDict] = []
        for p in proc_list:
            if isinstance(p, dict):
                result.append(
                    ProcessEntryDict(
                        pid=p.get("pid", 0),
                        name=p.get("name", ""),
                        cpu_percent=p.get("cpu_percent", 0.0),
                        memory_info=p.get("memory_rss", 0),
                        status=p.get("status", ""),
                        num_threads=p.get("num_threads", 0),
                        username=p.get("username"),
                        ppid=p.get("ppid"),
                        create_time=p.get("create_time"),
                        exe=p.get("exe"),
                    )
                )
        return result

    def get_sensors(self) -> dict[str, list[float]]:
        """Temperatures keyed by sensor name → list of values."""
        if not self._check(Permission.SENSORS_READ):
            return {}
        state = self._state
        sens_container = state.get("sensors", {})
        sensor_list = sens_container.get("metrics", []) if isinstance(sens_container, dict) else []
        temps: dict[str, list[float]] = {}
        for s in sensor_list:
            if isinstance(s, dict):
                name = str(s.get("name", "unknown"))
                value = float(s.get("value", 0.0))
                temps.setdefault(name, []).append(value)
        return temps

    def get_system_load(self) -> SystemLoadDict:
        """CPU load percent, process / thread / handle counts."""
        if not self._check(Permission.SYSTEM_READ):
            return SystemLoadDict(cpu_percent=0.0, processes=0, threads=0, handles=0)
        state = self._state
        cpu = state.get("cpu", {})
        assert isinstance(cpu, dict)
        metrics = cpu.get("metrics", [{}])
        agg = metrics[0] if metrics else {}
        proc_container = state.get("processes", {})
        proc_list = proc_container.get("metrics", []) if isinstance(proc_container, dict) else []
        return SystemLoadDict(
            cpu_percent=agg.get("usage_percent", 0.0),
            processes=len(proc_list) if isinstance(proc_list, list) else 0,
            threads=0,
            handles=0,
        )

    def get_static_info(self) -> StaticInfoDict:
        """Static system info from the active driver (or defaults)."""
        if not self._check(Permission.SYSTEM_READ):
            return StaticInfoDict()
        driver = self._driver
        static = None
        if driver is not None and hasattr(driver, "get_static_info"):
            try:
                static = driver.get_static_info()
            except Exception:
                pass
        if static is not None:
            return _dump(static)
        return StaticInfoDict()

    def get_boot_time(self) -> float:
        """Boot timestamp as a float (or 0.0 when unavailable)."""
        if not self._check(Permission.SYSTEM_READ):
            return 0.0
        driver = self._driver
        if driver is not None:
            try:
                static = driver.get_static_info()
                if static is not None:
                    bt = static.system.boot_time
                    if not isinstance(bt, UnavailableInfo):
                        return datetime.datetime.fromisoformat(str(bt)).timestamp()
            except Exception:
                pass
        return 0.0

    def get_disk_partitions(self) -> list[dict[str, str]]:
        """Partition list derived from engine storage data."""
        if not self._check(Permission.DISK_READ):
            return []
        state = self._state
        storage_container = state.get("storage", {})
        storage_list = storage_container.get("metrics", []) if isinstance(storage_container, dict) else []
        return [
            {
                "device": "",
                "mountpoint": s.get("mount_point", "") if isinstance(s, dict) else "",
                "fstype": "",
            }
            for s in (storage_list or [])
        ]

    def get_network_interfaces(self) -> dict[str, object]:
        """Network interfaces from static info (or empty dict when unavailable)."""
        if not self._check(Permission.NETWORK_READ):
            return {}
        try:
            static = self.get_static_info()
            if static:
                raw = static.get("network", {}).get("interfaces", [])
                if raw:
                    result: dict[str, object] = {}
                    for iface in raw:
                        name = iface.get("name", "")
                        if name:
                            result[name] = iface
                    return result
        except Exception:
            pass
        return {}

    def get_battery(self) -> BatteryDict:
        """Battery charge / status dict."""
        if not self._check(Permission.BATTERY_READ):
            return BatteryDict(percent=0.0, power_plugged=None, seconds_left=None)
        state = self._state
        bat_container = state.get("battery")
        if bat_container is None:
            return BatteryDict(percent=0.0, power_plugged=None, seconds_left=None)
        if isinstance(bat_container, dict):
            metrics = bat_container.get("metrics", [{}])
            bat = metrics[0] if metrics else {}
            return BatteryDict(
                percent=bat.get("percent", 0.0),
                power_plugged=bat.get("power_plugged"),
                seconds_left=bat.get("seconds_left"),
            )
        return BatteryDict(percent=0.0, power_plugged=None, seconds_left=None)

    # ------------------------------------------------------------------
    # Aggregate
    # ------------------------------------------------------------------

    def get_all(self) -> AggregatedStateDict:
        """Aggregate all metrics into a single TypedDict."""
        return AggregatedStateDict(
            cpu=self.get_cpu_metrics(),
            memory=self.get_memory_metrics(),
            disks=[self.get_disk_usage("/")],
            network=self.get_network_io(),
            processes=self.get_process_list(),
            sensors={"temperatures": []},
            battery=self.get_battery(),
            boot_time=self.get_boot_time(),
            load=self.get_system_load(),
            static_info=self.get_static_info(),
        )

    # ------------------------------------------------------------------
    # Process management  (delegates to driver.manage_process)
    # ------------------------------------------------------------------

    def terminate_process(self, pid: int) -> bool:
        """Request graceful process termination.  Returns success."""
        if not self._check(Permission.PROCESSES_WRITE):
            return False
        return self._manage_process(pid, "terminate")

    def kill_process(self, pid: int) -> bool:
        """Force-kill a process.  Returns success."""
        if not self._check(Permission.PROCESSES_EXECUTE):
            return False
        return self._manage_process(pid, "kill")

    def _manage_process(self, pid: int, action: str) -> bool:
        driver = self._driver
        if driver is not None and hasattr(driver, "manage_process"):
            try:
                return bool(driver.manage_process(pid, action))
            except Exception:
                pass
        return False

    # ------------------------------------------------------------------
    # Script management  (delegates to engine script API)
    # ------------------------------------------------------------------

    def get_scripts(self) -> list[ScriptInfo]:
        """Return metadata for all loaded scripts."""
        if not self._check(Permission.SCRIPT_READ):
            return []
        if self._engine is None:
            return []
        try:
            return self._engine.list_scripts()
        except Exception:
            return []

    def set_script_mode(self, name: str, mode: ScriptExecutionMode) -> None:
        """Change a script's execution mode by name."""
        if self._engine is None:
            return
        try:
            self._engine.set_script_execution_mode(name, mode)
        except Exception:
            pass

    def set_script_permissions(
        self, name: str, permissions: list[Permission]
    ) -> None:
        """Update a script's allowed permissions by name."""
        if self._engine is None:
            return
        try:
            self._engine.set_script_permissions(name, permissions)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Config read/write  (delegates to engine config API)
    # ------------------------------------------------------------------

    def read_config(self) -> dict[str, Any]:
        """Read the full config from the engine."""
        if self._engine is None:
            return {}
        return self._engine.get_config()

    def write_config(self, key: str, value: Any) -> None:
        """Write a single config value through the engine."""
        if self._engine is None:
            raise RuntimeError("EngineBridge has no engine reference")
        self._engine.set_config(key, value)
        self.config_changed_signal.emit({key: value})


# ------------------------------------------------------------------
# Module-level singleton  —  caller must instantiate with a parent
# ------------------------------------------------------------------
bridge: EngineBridge | None = None
