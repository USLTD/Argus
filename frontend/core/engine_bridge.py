from __future__ import annotations

from typing import Any


class EngineBridge:
    """Wraps BackendEngine and exposes typed dict methods for frontend consumption.

    When an engine is available, each method delegates to
    ``engine.get_system_state()`` (and optionally the active driver for
    static info / process management).  When no engine is available
    (e.g. during tests or startup) sensible defaults are returned.

    This class does **not** import or fall back to *psutil* — it is a
    pure pass-through to engine state.
    """

    def __init__(self, engine: Any = None) -> None:
        self._engine = engine

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @property
    def _state(self) -> dict[str, Any]:
        if self._engine is None:
            return {}
        try:
            return self._engine.get_system_state()
        except Exception:
            return {}

    @property
    def _driver(self) -> Any:
        if self._engine is None:
            return None
        return getattr(getattr(self._engine, "loader", None), "active_driver", None)

    # ------------------------------------------------------------------
    # Public API  —  all return plain dicts for loose coupling
    # ------------------------------------------------------------------

    def get_cpu_metrics(self) -> dict[str, Any]:
        """CPU usage, per-core breakdown, frequency and core counts."""
        state = self._state
        cpu = state.get("cpu", {})
        return {
            "cpu_percent": cpu.get("usage_percent", 0.0),
            "per_core": [],
            "frequency": None,
            "physical_cores": cpu.get("physical_cores", 0),
            "logical_cores": cpu.get("logical_cores", 0),
        }

    def get_memory_metrics(self) -> dict[str, Any]:
        """RAM totals, usage, available, free, cached and percent."""
        state = self._state
        ram = state.get("ram", {})
        total = ram.get("total_bytes", 0)
        used = ram.get("used_bytes", 0)
        available = ram.get("available_bytes", 0)
        percent = ram.get("percent", 0.0)
        return {
            "total": total,
            "used": used,
            "available": available,
            "free": available,  # engine reports 'available' as free
            "cached": 0,
            "percent": percent,
        }

    def get_disk_usage(self, path: str) -> dict[str, Any]:
        """Usage stats for *path* (total / used / free bytes + percent)."""
        state = self._state
        storage_list = state.get("storage", [])
        for disk in storage_list:
            if isinstance(disk, dict) and disk.get("mount_point", "") == path:
                return {
                    "total": disk.get("total_bytes", 0),
                    "used": disk.get("used_bytes", 0),
                    "free": disk.get("free_bytes", 0),
                    "percent": disk.get("percent", 0.0),
                }
        return {"total": 0, "used": 0, "free": 0, "percent": 0.0}

    def get_network_io(self) -> dict[str, Any]:
        """Aggregate bytes sent / received across all interfaces."""
        state = self._state
        net_list = state.get("network", [])
        total_sent = 0
        total_recv = 0
        for iface in net_list:
            if isinstance(iface, dict):
                total_sent += iface.get("bytes_sent", 0)
                total_recv += iface.get("bytes_recv", 0)
        return {"bytes_sent": total_sent, "bytes_recv": total_recv}

    def get_process_list(self) -> list[dict[str, Any]]:
        """Snapshot of running processes (limited fields)."""
        state = self._state
        proc_list = state.get("processes", [])
        result: list[dict[str, Any]] = []
        for proc in proc_list:
            if isinstance(proc, dict):
                result.append(
                    {
                        "pid": proc.get("pid", 0),
                        "name": proc.get("name", ""),
                        "cpu_percent": proc.get("cpu_percent", 0.0),
                        "memory_info": proc.get("memory_rss", 0),
                        "status": proc.get("status", ""),
                        "num_threads": proc.get("num_threads", 0),
                        "username": proc.get("username"),
                        "ppid": proc.get("ppid"),
                        "create_time": proc.get("create_time"),
                        "exe": proc.get("exe"),
                    }
                )
        return result

    def get_sensors(self) -> dict[str, Any]:
        """Temperatures keyed by sensor name → list of values."""
        state = self._state
        sensor_list = state.get("sensors", [])
        temps: dict[str, list[float]] = {}
        for s in sensor_list:
            if isinstance(s, dict):
                name = s.get("name", "unknown")
                value = s.get("value", 0.0)
                temps.setdefault(name, []).append(float(value))
        return temps

    def get_system_load(self) -> dict[str, Any]:
        """CPU load percent, process / thread / handle counts."""
        state = self._state
        cpu = state.get("cpu", {})
        proc_list = state.get("processes", [])
        return {
            "cpu_percent": cpu.get("usage_percent", 0.0),
            "processes": len(proc_list) if isinstance(proc_list, list) else 0,
            "threads": 0,
            "handles": 0,
        }

    def get_static_info(self) -> dict[str, Any]:
        """Static system info from the active driver (or defaults)."""
        driver = self._driver
        static = None
        if driver is not None and hasattr(driver, "get_static_info"):
            try:
                static = driver.get_static_info()
            except Exception:
                pass
        if static is not None:
            if hasattr(static, "model_dump"):
                return static.model_dump()
            return dict(static)
        return {
            "hostname": "",
            "os_name": "",
            "os_version": "",
            "architecture": "",
            "cpu_brand": "",
            "cpu_physical_cores": 0,
            "cpu_logical_cores": 0,
            "cpu_frequency_mhz": None,
            "total_ram_bytes": 0,
            "python_version": "",
            "boot_time": "",
        }

    def get_boot_time(self) -> float:
        """Boot timestamp as a float (or 0.0 when unavailable)."""
        # The engine does not expose boot time yet — return 0.0
        # so callers can detect "unavailable" without crashing.
        return 0.0

    def get_disk_partitions(self) -> list[dict[str, Any]]:
        """Partition list derived from engine storage data."""
        state = self._state
        storage_list = state.get("storage", [])
        return [
            {
                "device": "",
                "mountpoint": s.get("mount_point", "") if isinstance(s, dict) else "",
                "fstype": "",
            }
            for s in (storage_list or [])
        ]

    def get_network_interfaces(self) -> dict[str, Any]:
        """Network interface → addresses (not yet provided by engine)."""
        return {}

    def get_battery(self) -> dict[str, Any]:
        """Battery charge / status dict."""
        state = self._state
        bat = state.get("battery")
        if bat is None:
            return {"percent": 0.0, "power_plugged": None, "seconds_left": None}
        if isinstance(bat, dict):
            return {
                "percent": bat.get("percent", 0.0),
                "power_plugged": bat.get("power_plugged"),
                "seconds_left": bat.get("seconds_left"),
            }
        return {"percent": 0.0, "power_plugged": None, "seconds_left": None}

    # ------------------------------------------------------------------
    # Process management  (delegates to driver.manage_process)
    # ------------------------------------------------------------------

    def terminate_process(self, pid: int) -> bool:
        """Request graceful process termination.  Returns success."""
        return self._manage_process(pid, "terminate")

    def kill_process(self, pid: int) -> bool:
        """Force-kill a process.  Returns success."""
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
# Module-level singleton
# ------------------------------------------------------------------
bridge = EngineBridge()
