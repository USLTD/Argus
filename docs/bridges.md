# Bridge API Reference

Three bridge classes provide the data-access layer between backend drivers and frontend consumers. The bridges share the same output contracts (dict shapes) but differ in execution model.

- **SyncBridge** -- synchronous, tick-before-read. Used by `main_tui.py` (Textual TUI).
- **AsyncBridge** -- asyncio-native, auto-tick on every read. Intended for async consumers (web API, CLI tools).
- **EngineBridge** -- PyQt6 QObject with timer-based polling and signal emission. Used by `main_gui.py`.

---

## SyncBridge

**Location**: `backend/bridges/sync_bridge.py`
**Used by**: Textual TUI and CLI tools.

A thin synchronous wrapper around a `BaseDriver`. Every `get_*()` method reads from the most recent snapshot; call `tick_all()` to refresh the snapshot before reading.

### Constructor

```python
from backend.bridges.sync_bridge import SyncBridge
from backend.core.engine import BackendEngine

engine = BackendEngine()
bridge = SyncBridge(driver=engine.loader.active_driver)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `driver` | `BaseDriver` | An active backend driver instance |

### Lifecycle

```python
def tick_all(self) -> None:
```

Refresh all metrics from the driver. Must be called before reading data. Creates a `DriverContext`, calls `driver.tick(ctx)`, and stores the resulting `TickSnapshot` internally.

### Per-metric Getters

All `get_*()` methods return flat dicts. If no snapshot exists (tick not yet called) or the underlying data is `Unavailable`, they return zero/empty defaults.

```python
def get_cpu_metrics(self) -> dict:
```

```python
{
    "cpu_percent": 45.2,      # float -- aggregate usage %
    "per_core": [34.5, 56.1], # list[float] -- per-core usage %
    "frequency": 2400.0,      # float | None -- MHz
    "physical_cores": 4,      # int -- from driver.get_static_info()
    "logical_cores": 8,       # int -- from driver.get_static_info()
}
```

```python
def get_memory_metrics(self) -> dict:
```

```python
{
    "total": 17179869184,     # int -- bytes
    "used": 8589934592,       # int -- bytes
    "available": 8589934592,  # int -- bytes (same as free)
    "free": 8589934592,       # int -- bytes (reports available_bytes)
    "cached": 0,              # int -- bytes (always 0, not yet instrumented)
    "percent": 50.0,          # float
}
```

```python
def get_disk_usage(self, path: str = "/") -> dict:
```

Searches the snapshot disk metrics for the entry matching `path`. Returns the first match or zero-filled defaults.

```python
{
    "total": 500107862016,    # int -- bytes
    "used": 250053931008,     # int -- bytes
    "free": 250053931008,     # int -- bytes
    "percent": 50.0,          # float
}
```

```python
def get_network_io(self) -> dict:
```

Aggregates bytes sent/received across all network interfaces.

```python
{
    "bytes_sent": 1048576,    # int
    "bytes_recv": 2097152,    # int
}
```

```python
def get_process_list(self) -> list[dict]:
```

```python
[
    {
        "pid": 1234,              # int
        "name": "python",         # str
        "cpu_percent": 2.5,       # float
        "memory_info": 45678901,  # int -- RSS bytes
        "status": "running",      # str
        "num_threads": 0,         # int (always 0, not yet instrumented)
        "username": "user",       # str | None
        "ppid": None,             # int | None (always None)
        "create_time": None,      # float | None (always None)
        "exe": None,              # str | None (always None)
    }
]
```

```python
def get_sensors(self) -> dict:
```

Groups sensor readings by name.

```python
{
    "temperatures": {
        "core_0": [45.0, 46.5],  # dict[str, list[float]]
    }
}
```

```python
def get_battery(self) -> dict:
```

```python
{
    "percent": 85.0,          # float
    "power_plugged": True,    # bool | None
    "seconds_left": 7200.0,   # float | None
}
```

### Static Info

```python
def get_static_info(self) -> dict:
```

Reads from `driver.get_static_info()`. Falls back to empty fields if the driver returns `None`.

```python
{
    "hostname": "my-pc",          # str
    "platform": "Linux",          # str
    "platform_version": "...",    # str
    "cpu_brand": "Intel Core...", # str
    "cpu_physical_cores": 4,      # int
    "cpu_logical_cores": 8,       # int
    "total_ram": 17179869184,     # int -- bytes
}
```

```python
def get_boot_time(self) -> float:
```

Returns Unix timestamp of last boot from `driver.get_static_info().boot_time`, or `0.0`.

### Process Management

```python
def terminate_process(self, pid: int) -> bool:
```

Calls `driver.manage_process(pid, "terminate")`. Returns `True` on success, `False` on exception.

```python
def kill_process(self, pid: int) -> bool:
```

Calls `driver.manage_process(pid, "kill")`. Returns `True` on success, `False` on exception.

### Aggregate

```python
def get_all(self) -> dict:
```

Returns all metrics from one fresh tick as a single dict. **Caller does not need to call `tick_all()` first** -- this method calls it internally, then invokes every individual `get_*()` method in sequence.

```python
{
    "cpu":         { ... },   # get_cpu_metrics()
    "memory":      { ... },   # get_memory_metrics()
    "disk":        { ... },   # get_disk_usage("/")
    "network":     { ... },   # get_network_io()
    "processes":   [ ... ],   # get_process_list()
    "sensors":     { ... },   # get_sensors()
    "battery":     { ... },   # get_battery()
    "static_info": { ... },   # get_static_info()
    "boot_time":   12345.0,   # get_boot_time()
}
```

---

## AsyncBridge

**Location**: `backend/bridges/async_bridge.py`
**Intended for**: Future async consumers (web API, async CLI tools).

Same per-metric API as SyncBridge but all `get_*()` methods are `async` and call `await self.tick_all()` internally for fresh data on each read. Blocking driver calls run in a thread executor via `loop.run_in_executor()`.

### Constructor

```python
from backend.bridges.async_bridge import AsyncBridge
from backend.core.engine import BackendEngine

engine = BackendEngine()
bridge = AsyncBridge(driver=engine.loader.active_driver)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `driver` | `BaseDriver` | An active backend driver instance |

### Lifecycle

```python
async def tick_all(self) -> None:
```

Refreshes all metrics from the driver in a thread executor so the event loop stays unblocked.

```python
async def start_polling(self, interval: float = 2.0) -> None:
```

Starts a background `asyncio.Task` that calls `tick_all()` every `interval` seconds. Errors are silently swallowed to keep polling alive. Safe to call multiple times -- subsequent calls are no-ops while a poll task is active.

```python
async def stop_polling(self) -> None:
```

Cancels the background polling task and sets the task reference to `None`.

```python
@property
def snapshot(self) -> TickSnapshot | None:
```

Returns the latest `TickSnapshot`, or `None` if never ticked.

### Per-metric Getters

Every `get_*()` method first calls `await self.tick_all()`, then reads from `self._snapshot`. Return dict shapes are identical to SyncBridge.

```python
async def get_cpu_metrics(self) -> dict:
async def get_memory_metrics(self) -> dict:
async def get_disk_usage(self, path: str = "/") -> dict:
async def get_network_io(self) -> dict:
async def get_process_list(self) -> list[dict]:
async def get_sensors(self) -> dict:
async def get_battery(self) -> dict:
async def get_static_info(self) -> dict:
async def get_boot_time(self) -> float:
```

### Process Management

```python
async def terminate_process(self, pid: int) -> bool:
async def kill_process(self, pid: int) -> bool:
```

Both call `self._driver.manage_process()` synchronously in the calling task. These are **not** wrapped in a thread executor -- they block the current coroutine but should be fast since the driver call is typically a local syscall.

### Aggregate

```python
async def get_all(self) -> dict:
```

Calls `tick_all()` once, then reads every metric directly from the snapshot using the converter functions (does NOT call the individual `get_*()` methods). Note: `get_all()` passes `static_cores=0, static_threads=0` to `cpu_collection_to_dict`, so the returned CPU dict will always show `physical_cores: 0` and `logical_cores: 0`.

```python
{
    "cpu":     { ... },
    "memory":  { ... },
    "disk":    { ... },
    "network": { ... },
    "processes": [ ... ],
    "sensors": { ... },
    "battery": { ... },
}
```

### Usage Example

```python
import asyncio
from backend.bridges.async_bridge import AsyncBridge
from backend.core.engine import BackendEngine

async def main():
    engine = BackendEngine()
    bridge = AsyncBridge(driver=engine.loader.active_driver)

    await bridge.start_polling(2.0)

    # After polling has run for a bit:
    cpu = await bridge.get_cpu_metrics()
    print(f"CPU: {cpu['cpu_percent']}%")

    await bridge.stop_polling()

asyncio.run(main())
```

---

## EngineBridge

**Location**: `frontend/core/engine_bridge.py`
**Used by**: `main_gui.py` (PyQt6 GUI)
**Extends**: `QObject`

EngineBridge is a PyQt6 QObject that owns a `QTimer` and emits a signal on each tick. It wraps a `BackendEngine` (not a raw driver) and reads system state through `engine.get_system_state()`. Every getter returns a typed dict.

### Constructor

```python
from frontend.core.engine_bridge import EngineBridge

engine = BackendEngine()
bridge = EngineBridge(engine=engine, parent=None)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `engine` | `object` | A BackendEngine instance (duck-typed, must expose `.loader.active_driver` and `.get_system_state()`) |
| `parent` | `QObject | None` | Optional Qt parent for memory management |

### Signal

```
state_updated = pyqtSignal(BridgeContext)
```

Emitted on every timer tick. The `BridgeContext` object has `.data` (the `AggregatedStateDict`) and `.bridge` (the `EngineBridge` instance).

### Lifecycle

```python
def start_polling(self, interval_ms: int = 1000) -> None:
```

Starts the internal `QTimer` with the given interval in milliseconds (default 1000).

```python
def stop_polling(self) -> None:
```

Stops the internal `QTimer`.

### Per-metric Getters

These read from `engine.get_system_state()` and return typed dicts. Unlike the backend bridges, they do NOT call `tick_all()` -- they read pre-aggregated dicts from the engine's state.

```python
def get_cpu_metrics(self) -> CpuMetricsDict:
```

```python
{
    "cpu_percent": 45.2,      # float
    "per_core": [34.5, 56.1], # list[float]
    "frequency": 2400.0,      # float | None -- MHz
    "physical_cores": 4,      # int
    "logical_cores": 8,       # int
}
```

```python
def get_memory_metrics(self) -> MemoryMetricsDict:
```

```python
{
    "total": 17179869184,     # int -- bytes
    "used": 8589934592,       # int -- bytes
    "available": 8589934592,  # int -- bytes
    "free": 8589934592,       # int -- bytes (same as available)
    "cached": 0,              # int -- bytes
    "percent": 50.0,          # float
}
```

```python
def get_disk_usage(self, path: str) -> DiskUsageDict:
```

**Note**: Unlike SyncBridge/AsyncBridge, this method requires `path` as a positional argument (no default). Searches the engine's storage metrics for the matching mount point.

```python
{
    "total": 500107862016,    # int -- bytes
    "used": 250053931008,     # int -- bytes
    "free": 250053931008,     # int -- bytes
    "percent": 50.0,          # float
}
```

```python
def get_network_io(self) -> NetworkIODict:
```

```python
{
    "bytes_sent": 1048576,    # int
    "bytes_recv": 2097152,    # int
}
```

```python
def get_process_list(self) -> list[ProcessEntryDict]:
```

```python
[
    {
        "pid": 1234,              # int
        "name": "python",         # str
        "cpu_percent": 2.5,       # float
        "memory_info": 45678901,  # int -- RSS bytes
        "status": "running",      # str
        "num_threads": 0,         # int
        "username": "user",       # str | None
        "ppid": None,             # int | None
        "create_time": None,      # float | None
        "exe": None,              # str | None
    }
]
```

```python
def get_sensors(self) -> dict[str, list[float]]:
```

```python
{
    "core_0": [45.0, 46.5],  # dict[str, list[float]]
}
```

Note: Unlike the backend bridges, this returns the sensor dict directly (no `"temperatures"` wrapper key).

```python
def get_battery(self) -> BatteryDict:
```

```python
{
    "percent": 85.0,          # float
    "power_plugged": True,    # bool | None
    "seconds_left": 7200.0,   # float | None
}
```

```python
def get_system_load(self) -> SystemLoadDict:
```

EngineBridge-only method. Returns CPU load percent plus process/thread/handle counts.

```python
{
    "cpu_percent": 45.2,  # float
    "processes": 234,     # int -- count from process list
    "threads": 0,         # int (not yet instrumented)
    "handles": 0,         # int (not yet instrumented)
}
```

### Static Info

```python
def get_static_info(self) -> StaticInfoDict:
```

Reads from `driver.get_static_info()` through the engine. Falls back to empty strings/zeros.

```python
{
    "hostname": "my-pc",            # str
    "os_name": "Linux",            # str
    "os_version": "24.04 LTS",     # str
    "architecture": "x86_64",      # str
    "cpu_brand": "Intel Core...",  # str
    "cpu_physical_cores": 4,       # int
    "cpu_logical_cores": 8,        # int
    "cpu_frequency_mhz": 2400.0,   # float | None
    "total_ram_bytes": 17179869184, # int
    "python_version": "3.12.0",    # str
    "boot_time": "2025-06-25...",  # str
}
```

```python
def get_boot_time(self) -> float:
```

**Always returns `0.0`** in the current implementation.

### Additional Info Methods

```python
def get_disk_partitions(self) -> list[dict[str, str]]:
```

Returns a list of partition dicts derived from engine storage data:

```python
[
    {
        "device": "",                    # str (not yet populated)
        "mountpoint": "/",               # str
        "fstype": "",                    # str (not yet populated)
    }
]
```

```python
def get_network_interfaces(self) -> dict[str, object]:
```

**Returns an empty dict** -- not yet provided by the engine.

### Process Management

```python
def terminate_process(self, pid: int) -> bool:
def kill_process(self, pid: int) -> bool:
```

Both delegate to `driver.manage_process(pid, action)`. Returns `True` on success, `False` if the driver is not available or raises.

### Aggregate

```python
def get_all(self) -> AggregatedStateDict:
```

Aggregates all metrics into a single `AggregatedStateDict`. Called internally by the timer on each tick.

```python
{
    "cpu":         CpuMetricsDict,
    "memory":      MemoryMetricsDict,
    "disks":       [DiskUsageDict],    # list -- note: plural "disks"
    "network":     NetworkIODict,
    "processes":   [ProcessEntryDict],
    "sensors":     {"temperatures": []},  # always empty in current impl
    "battery":     BatteryDict,
    "boot_time":   0.0,               # always 0.0
    "load":        SystemLoadDict,
    "static_info": StaticInfoDict,
}
```

**Note about `get_all()` in EngineBridge**: The `sensors` field is always `{"temperatures": []}` regardless of actual sensor data -- the private `_tick()` method does not call `get_sensors()`.

### Usage Pattern

```python
from frontend.core.engine_bridge import EngineBridge
from backend.core.engine import BackendEngine
from backend.interfaces.contexts import BridgeContext

engine = BackendEngine()
bridge = EngineBridge(engine)

def on_update(ctx: BridgeContext):
    data = ctx.data  # AggregatedStateDict
    print(f"CPU: {data['cpu']['cpu_percent']}%")

bridge.state_updated.connect(on_update)
bridge.start_polling(interval_ms=2000)
```

---

## Converters

**Location**: `backend/bridges/converters.py`

Seven pure functions that transform `MetricsCollection[T]` objects into the flat dicts consumed by the bridges. These functions have zero GUI dependencies and are shared by SyncBridge and AsyncBridge. (EngineBridge reads engine state directly and does not use converters.)

| Function | Input | Output | Unavailable fallback |
|----------|-------|--------|----------------------|
| `cpu_collection_to_dict(cpu, static_cores, static_threads)` | `MetricsCollection[CPUMetric]` | CPU flat dict | `cpu_percent: 0.0`, `per_core: []`, `frequency: None` |
| `memory_collection_to_dict(memory)` | `MetricsCollection[MemoryMetric]` | Memory flat dict | all fields zero |
| `disk_collection_to_dict(disk, mount_point)` | `MetricsCollection[StorageMetric]` | Disk flat dict | all fields zero |
| `network_collection_to_dict(network)` | `MetricsCollection[NetworkMetric]` | Network flat dict | `bytes_sent: 0`, `bytes_recv: 0` |
| `process_collection_to_dict(processes)` | `MetricsCollection[ProcessMetric]` | List of process dicts | empty list |
| `sensor_collection_to_dict(sensors)` | `MetricsCollection[SensorMetric]` | Sensor dict | `temperatures: {}` |
| `battery_collection_to_dict(battery)` | `MetricsCollection[BatteryMetric]` | Battery flat dict | `percent: 0.0`, `power_plugged: None`, `seconds_left: None` |

### Converter Details

```python
# CPU -- finds aggregate metric (core_id is None) and per-core metrics
cpu_collection_to_dict(cpu, static_cores=4, static_threads=8)
# Returns: {"cpu_percent": ..., "per_core": [...], "frequency": ..., "physical_cores": 4, "logical_cores": 8}

# Memory -- takes the first metric from the collection
memory_collection_to_dict(memory)
# Returns: {"total": ..., "used": ..., "available": ..., "free": ..., "cached": 0, "percent": ...}

# Disk -- searches for the matching mount_point
disk_collection_to_dict(disk, mount_point="/")
# Returns: {"total": ..., "used": ..., "free": ..., "percent": ...}

# Network -- sums bytes_sent and bytes_recv across all interfaces
network_collection_to_dict(network)
# Returns: {"bytes_sent": ..., "bytes_recv": ...}

# Processes -- maps each ProcessMetric to a flat dict
process_collection_to_dict(processes)
# Returns: [{"pid": ..., "name": ..., ...}]

# Sensors -- groups by sensor name
sensor_collection_to_dict(sensors)
# Returns: {"temperatures": {"core_0": [45.0, 46.5], ...}}

# Battery -- takes the first metric
battery_collection_to_dict(battery)
# Returns: {"percent": ..., "power_plugged": ..., "seconds_left": ...}
```

All converters accept the `Unavailable` sentinel as input and return zero/empty defaults, so callers never need to check for missing data before calling a converter.

---

## Output Contract Summary

| Field | SyncBridge | AsyncBridge | EngineBridge |
|-------|------------|-------------|--------------|
| `cpu` | `get_cpu_metrics()` | `await get_cpu_metrics()` | `get_cpu_metrics()` |
| `memory` / `ram` | `get_memory_metrics()` | `await get_memory_metrics()` | `get_memory_metrics()` |
| `disk` | `get_disk_usage(path)` | `await get_disk_usage(path)` | `get_disk_usage(path)` -- **required arg** |
| `network` | `get_network_io()` | `await get_network_io()` | `get_network_io()` |
| `processes` | `get_process_list()` | `await get_process_list()` | `get_process_list()` |
| `sensors` | `get_sensors()` | `await get_sensors()` | `get_sensors()` -- no `"temperatures"` key |
| `battery` | `get_battery()` | `await get_battery()` | `get_battery()` |
| `static_info` | `get_static_info()` | `await get_static_info()` | `get_static_info()` -- different fields |
| `boot_time` | `get_boot_time()` | `await get_boot_time()` | `get_boot_time()` -- always 0.0 |
| `load` | -- | -- | `get_system_load()` -- EngineBridge only |
| `disks` (plural) | -- | -- | `get_all()["disks"]` -- EngineBridge only |
| `get_all()` key | `"static_info"` included | static info NOT included | `"static_info"` included |

### Key Differences

1. **Polling model**: SyncBridge requires manual `tick_all()` calls. AsyncBridge offers optional `start_polling()`/`stop_polling()` but also auto-ticks on each `get_*()`. EngineBridge uses QTimer with signal emission.

2. **`get_all()` coverage**: AsyncBridge's `get_all()` passes `static_cores=0, static_threads=0` to CPU conversion (no static-info enrichment) and omits `static_info` and `boot_time`. EngineBridge's `get_all()` returns `disks` as a list (plural key) and includes `load` and `static_info`.

3. **EngineBridge constraints**: `get_boot_time()` always returns `0.0`. `get_sensors()` returns a flat dict without the `"temperatures"` wrapper. The `get_all()` call hardcodes `sensors` to `{"temperatures": []}`.
