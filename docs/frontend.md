# EngineBridge API Reference

EngineBridge wraps BackendEngine for PyQt6 frontends. It emits `state_updated` on a configurable timer and exposes typed `get_*()` methods so consumers never touch raw engine data. Every call returns a TypedDict with known fields and types.

---

## Constructor

```python
EngineBridge(
    engine: object = None,
    parent: QObject | None = None,
    permissions: set[Permission] | None = None,
) -> None
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `engine` | `object` | A `BackendEngine` instance. The bridge calls `engine.get_system_state()` to retrieve metrics on each tick. |
| `parent` | `QObject \| None` | Optional `QObject` parent for Qt memory management. |
| `permissions` | `set[Permission] \| None` | Access control set. `None` means unrestricted access (the frontend default). When a set is provided, each getter checks against the required `Permission` and returns safe defaults if denied. See [Permission Note](#permission-note). |

---

## Lifecycle

### `start_polling(interval_ms: int = 1000) -> None`

Starts the internal `QTimer`. On each tick the bridge fetches fresh engine state, caches it, emits `state_updated`, and all `get_*()` calls for the remainder of that cycle read from the same cached snapshot. Default interval is 1000 ms (1 second).

### `stop_polling() -> None`

Stops the timer and clears the internal cache. No further signals are emitted until `start_polling()` is called again.

---

## Signal

### `state_updated`

```python
state_updated = pyqtSignal(BridgeContext)
```

Emitted on every timer tick. The connected slot receives a `BridgeContext` object:

| Field | Type | Description |
|-------|------|-------------|
| `data` | `AggregatedStateDict` | The full aggregated state dict from `get_all()`. |
| `bridge` | `EngineBridge` | Reference to the bridge instance, so handlers can call individual `get_*()` methods. |

```python
ctx.data          # AggregatedStateDict
ctx.bridge        # EngineBridge
```

---

## Getter Methods

### 1. `get_cpu_metrics() -> CpuMetricsDict`

CPU usage, per-core breakdown, frequency, and core counts.

| Field | Type | Description |
|-------|------|-------------|
| `cpu_percent` | `float` | Overall CPU usage as a percentage. |
| `per_core` | `list[float]` | Per-core usage percentage values. |
| `frequency` | `float \| None` | Current CPU frequency in MHz, or `None` if unavailable. |
| `physical_cores` | `int` | Number of physical cores. |
| `logical_cores` | `int` | Number of logical cores (including hyper-threading). |

---

### 2. `get_memory_metrics() -> MemoryMetricsDict`

RAM totals, usage, and percent.

| Field | Type | Description |
|-------|------|-------------|
| `total` | `int` | Total physical RAM in bytes. |
| `used` | `int` | Used RAM in bytes. |
| `available` | `int` | Available RAM in bytes. |
| `free` | `int` | Free RAM in bytes (currently set to the same value as `available`). |
| `cached` | `int` | Cached memory in bytes. Currently reported as `0`. |
| `percent` | `float` | RAM usage as a percentage. |

---

### 3. `get_disk_usage(path: str) -> DiskUsageDict`

Usage statistics for a given mount point.

| Parameter | Type | Description |
|-----------|------|-------------|
| `path` | `str` | The mount point to query (e.g. `"/"` or `"C:\\"`). |

| Field | Type | Description |
|-------|------|-------------|
| `total` | `int` | Total disk space in bytes. |
| `used` | `int` | Used disk space in bytes. |
| `free` | `int` | Free disk space in bytes. |
| `percent` | `float` | Disk usage as a percentage. |

Returns zeroes if `path` is not found in the engine storage data.

---

### 4. `get_disk_partitions() -> list[dict[str, str]]`

Derives a partition list from engine storage data.

Each dict in the list contains:

| Field | Type | Description |
|-------|------|-------------|
| `device` | `str` | Device identifier. Currently always `""`. |
| `mountpoint` | `str` | Mount point from engine data. |
| `fstype` | `str` | Filesystem type. Currently always `""`. |

---

### 5. `get_network_io() -> NetworkIODict`

Aggregate bytes sent and received across all network interfaces.

| Field | Type | Description |
|-------|------|-------------|
| `bytes_sent` | `int` | Total bytes sent since system boot. |
| `bytes_recv` | `int` | Total bytes received since system boot. |

---

### 6. `get_network_interfaces() -> dict[str, object]`

Network interface names mapped to address data. Currently returns `{}` because the engine does not yet provide interface details.

---

### 7. `get_process_list() -> list[ProcessEntryDict]`

Snapshot of running processes with limited fields.

| Field | Type | Description |
|-------|------|-------------|
| `pid` | `int` | Process ID. |
| `name` | `str` | Process name. |
| `cpu_percent` | `float` | CPU usage as a percentage. |
| `memory_info` | `int` | RSS memory usage in bytes. |
| `status` | `str` | Process status (e.g. `"running"`, `"sleeping"`). |
| `num_threads` | `int` | Number of threads. |
| `username` | `str \| None` | Owner username, or `None` if unavailable. |
| `ppid` | `int \| None` | Parent process ID, or `None` if unavailable. |
| `create_time` | `float \| None` | Process creation timestamp (epoch), or `None` if unavailable. |
| `exe` | `str \| None` | Executable path, or `None` if unavailable. |

> **Performance note:** The process list is collected at most every 5th poll cycle (roughly every 5 seconds at the default 1 s interval) to reduce overhead.

---

### 8. `get_sensors() -> dict[str, list[float]]`

Temperature sensor readings keyed by sensor name.

```
{"core_0": [45.0, 46.5], "core_1": [44.0]}
```

| Return | Description |
|--------|-------------|
| `dict[str, list[float]]` | Sensor name mapped to a list of temperature values in Celsius. |

---

### 9. `get_system_load() -> SystemLoadDict`

CPU load percentage and system-level process, thread, and handle counts.

| Field | Type | Description |
|-------|------|-------------|
| `cpu_percent` | `float` | Overall CPU usage as a percentage. |
| `processes` | `int` | Number of running processes. |
| `threads` | `int` | Thread count. Currently always `0` (not yet collected). |
| `handles` | `int` | Handle count. Currently always `0` (not yet collected). |

---

### 10. `get_static_info() -> StaticInfoDict`

Static system information gathered once from the active driver.

| Field | Type | Description |
|-------|------|-------------|
| `hostname` | `str` | System hostname. |
| `os_name` | `str` | Operating system name. |
| `os_version` | `str` | Operating system version. |
| `architecture` | `str` | CPU architecture (e.g. `"x86_64"`, `"AMD64"`). |
| `cpu_brand` | `str` | CPU model name. |
| `cpu_physical_cores` | `int` | Number of physical CPU cores. |
| `cpu_logical_cores` | `int` | Number of logical CPU cores. |
| `cpu_frequency_mhz` | `float \| None` | CPU base frequency in MHz, or `None` if unavailable. |
| `total_ram_bytes` | `int` | Total installed RAM in bytes. |
| `python_version` | `str` | Python runtime version string. |
| `boot_time` | `str` | System boot time in ISO 8601 format. |

---

### 11. `get_boot_time() -> float`

System boot timestamp expressed as a Unix epoch float.

| Return | Description |
|--------|-------------|
| `float` | Boot timestamp. Currently always `0.0` (unused in the frontend). |

---

### 12. `get_battery() -> BatteryDict`

Battery charge level, AC status, and estimated remaining time.

| Field | Type | Description |
|-------|------|-------------|
| `percent` | `float` | Battery charge as a percentage. |
| `power_plugged` | `bool \| None` | `True` if AC power is connected, `False` if on battery, `None` if unknown. |
| `seconds_left` | `float \| None` | Estimated seconds until empty, or `None` if unknown. |

---

## `get_all()` and `AggregatedStateDict`

`get_all()` returns a single `AggregatedStateDict` containing every metric category.

```python
def get_all() -> AggregatedStateDict
```

| Field | Type | Source getter |
|-------|------|---------------|
| `cpu` | `CpuMetricsDict` | `get_cpu_metrics()` |
| `memory` | `MemoryMetricsDict` | `get_memory_metrics()` |
| `disks` | `list[DiskUsageDict]` | `[get_disk_usage("/")]` (root mount only) |
| `network` | `NetworkIODict` | `get_network_io()` |
| `processes` | `list[ProcessEntryDict]` | `get_process_list()` |
| `sensors` | `dict[str, list[float]]` | Always `{"temperatures": []}` (not yet wired) |
| `battery` | `BatteryDict` | `get_battery()` |
| `boot_time` | `float` | `get_boot_time()` |
| `load` | `SystemLoadDict` | `get_system_load()` |
| `static_info` | `StaticInfoDict` | `get_static_info()` |

---

## Performance Note

When `start_polling()` is active, the bridge caches the engine state once per tick cycle. Every `get_*()` call within that cycle reads from the same cached snapshot. There is no performance penalty for calling multiple getters in a signal handler, and the engine is queried exactly once per interval regardless of how many getters the frontend uses.

If the bridge is used without starting the timer, individual `get_*()` calls each query the engine independently.

---

## Permission Note

When `permissions=None` (the frontend default), every getter returns unrestricted data. When a `set[Permission]` is provided, each getter checks against the required permission using `PermissionHierarchy.grants()` and returns safe defaults (zeroes, empty lists, `None`) if the check fails.

| Getter | Required Permission |
|--------|-------------------|
| `get_cpu_metrics()` | `Permission.CPU_READ` |
| `get_memory_metrics()` | `Permission.MEMORY_READ` |
| `get_disk_usage()` | `Permission.DISK_READ` |
| `get_disk_partitions()` | `Permission.DISK_READ` |
| `get_network_io()` | `Permission.NETWORK_READ` |
| `get_network_interfaces()` | `Permission.NETWORK_READ` |
| `get_process_list()` | `Permission.PROCESSES_READ` |
| `get_sensors()` | `Permission.SENSORS_READ` |
| `get_system_load()` | `Permission.SYSTEM_READ` |
| `get_static_info()` | `Permission.SYSTEM_READ` |
| `get_boot_time()` | `Permission.SYSTEM_READ` |
| `get_battery()` | `Permission.BATTERY_READ` |

---

## Full Wiring Example

```python
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt6.QtCore import QObject
from backend.core.engine import BackendEngine
from frontend.core.engine_bridge import EngineBridge
from backend.interfaces.contexts import BridgeContext

app = QApplication([])
engine = BackendEngine()
bridge = EngineBridge(engine=engine)


class SystemMonitor(QObject):
    def __init__(self, bridge: EngineBridge) -> None:
        super().__init__()
        self._bridge = bridge
        self._label = QLabel("Waiting...")
        bridge.state_updated.connect(self._on_state)
        bridge.start_polling(interval_ms=2000)

    def _on_state(self, ctx: BridgeContext) -> None:
        cpu = ctx.bridge.get_cpu_metrics()
        mem = ctx.bridge.get_memory_metrics()
        self._label.setText(
            f"CPU: {cpu['cpu_percent']}%  |  "
            f"RAM: {mem['percent']}%"
        )


window = QMainWindow()
window.setCentralWidget(SystemMonitor(bridge)._label)
window.show()
app.exec()
```

This example creates an `EngineBridge`, connects `state_updated` to a handler that reads CPU and memory metrics from the bridge context, and updates a `QLabel` every 2 seconds.
