# Architecture

Argus is a modular system monitoring application with a clear separation between backend data collection, a bridge layer for data transformation, and multiple frontend rendering targets. The architecture emphasizes type safety, platform independence, and reusability across different UI paradigms.

## Layer Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ main_tui.py  │  │main_console  │  │   main_gui.py    │   │
│  │  (Textual)   │  │  (future)    │  │    (PyQt6)       │   │
│  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘   │
│         │                 │                    │             │
│         ▼                 ▼                    ▼             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ SyncBridge   │  │ AsyncBridge  │  │  EngineBridge    │   │
│  │  (sync)      │  │  (asyncio)   │  │ (QTimer+pyqtSig) │   │
│  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘   │
│         │                 │                    │             │
└─────────┼─────────────────┼────────────────────┼─────────────┘
          │                 │                    │
          ▼                 ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│                    Bridge Layer (backend/bridges/)            │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                   converters.py                         │ │
│  │   MetricsCollection[T] | Unavailable  ──►  dict         │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       Backend Layer                          │
│  ┌──────────────┐  ┌────────────────┐  ┌────────────────┐  │
│  │  BaseDriver  │  │ BackendEngine  │  │  DriverContext │  │
│  │   tick()     │  │  + loader      │  │  + HookSystem  │  │
│  └──────────────┘  └────────────────┘  └────────────────┘  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              caps.py (data models)                      │ │
│  │   CPUMetric, MemoryMetric, TickSnapshot, etc.          │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure

```
Argus/
├── main_tui.py             # Textual TUI entry point (synchronous)
├── main_gui.py             # PyQt6 GUI entry point
├── main_console.py         # Future CLI / console entry point
├── backend/
│   ├── bridges/
│   │   ├── converters.py   # MetricsCollection[T] → flat dicts
│   │   ├── sync_bridge.py  # Synchronous bridge (Textual)
│   │   └── async_bridge.py # Asyncio bridge (future consumers)
│   ├── core/
│   │   ├── engine.py       # BackendEngine orchestrator
│   │   └── loader.py       # DiscoveryLoader (driver discovery)
│   ├── interfaces/
│   │   ├── caps.py         # Pydantic models (CPUMetric, etc.)
│   │   ├── contexts.py     # Hook system contexts
│   │   ├── plugins.py      # BaseDriver, BasePlugin ABCs
│   │   ├── sentinels.py    # Unavailable, TickSnapshot
│   │   ├── rules.py        # Compatibility rules engine
│   │   └── enums.py        # Permission, ConfidenceScore enums
│   └── storage/
│       ├── config.py       # ArgusConfig
│       └── database.py     # DatabaseManager
├── frontend/
│   ├── core/
│   │   └── engine_bridge.py # PyQt6 EngineBridge (QObject)
│   ├── pages/              # Page widgets (PyQt6)
│   ├── graphs/             # Chart widgets (PyQt6)
│   ├── ui/                 # Shared UI components (PyQt6)
│   ├── themes/             # Theme definitions
│   └── assets/             # Icons, resources
├── drivers/
│   ├── generic_linux.py    # Linux driver
│   └── generic_windows.py  # Windows driver
├── docs/
│   └── architecture.md     # This file
└── tests/                  # Test suite
```

## Data Flow

The core data flow is a pipeline with four stages:

```
Driver tick → TickSnapshot → Converters → Flat dicts → UI render
```

### 1. Driver Tick

Every subsystem is collected by a dedicated method on `BaseDriver`. The aggregate method `tick()` calls each per-subsystem method and assembles the results into a single `TickSnapshot`.

```python
# backend/interfaces/plugins.py (BaseDriver.tick)
def tick(self, ctx: DriverContext) -> TickSnapshot:
    return TickSnapshot(
        cpu=self.tick_cpu(ctx),
        memory=self.tick_memory(ctx),
        processes=self.tick_processes(ctx),
        disk=self.tick_disk(ctx),
        network=self.tick_network(ctx),
        gpu=self.tick_gpu(ctx),
        sensors=self.tick_sensors(ctx),
        battery=self.tick_battery(ctx),
    )
```

Each per-subsystem method returns either a `MetricsCollection[T]` (concrete data) or the `Unavailable` sentinel. This means a driver can support any subset of subsystems without raising errors. A Linux driver might support CPU, memory, and processes, while a Windows driver adds battery and sensors.

### 2. TickSnapshot

`TickSnapshot` is a frozen dataclass with one field per subsystem:

```python
@dataclass
class TickSnapshot:
    cpu: MetricsCollection[CPUMetric] | Unavailable
    memory: MetricsCollection[MemoryMetric] | Unavailable
    processes: MetricsCollection[ProcessMetric] | Unavailable
    disk: MetricsCollection[StorageMetric] | Unavailable
    network: MetricsCollection[NetworkMetric] | Unavailable
    gpu: MetricsCollection[GPUMetric] | Unavailable
    sensors: MetricsCollection[SensorMetric] | Unavailable
    battery: MetricsCollection[BatteryMetric] | Unavailable
```

Every field is typed as a union with `Unavailable`. The frontend never sees raw exceptions. It always gets either data or a sentinel.

### 3. Converter Functions (Bridge Layer)

The bridge layer sits between the backend and the frontend. It converts typed `MetricsCollection[T]` objects into plain dicts that any UI toolkit can consume without importing Pydantic.

```python
# backend/bridges/converters.py (example)
def cpu_collection_to_dict(
    cpu: "MetricsCollection[CPUMetric] | UnavailableType",
    static_cores: int = 0,
    static_threads: int = 0,
) -> dict:
    from backend.interfaces.sentinels import Unavailable
    if isinstance(cpu, Unavailable):
        return {"cpu_percent": 0.0, "per_core": [], "frequency": None,
                "physical_cores": static_cores, "logical_cores": static_threads}
    metrics = cpu.metrics
    aggregate = next((m for m in metrics if m.core_id is None), None)
    per_core = [m.usage_percent for m in metrics if m.core_id is not None]
    return {
        "cpu_percent": aggregate.usage_percent if aggregate else 0.0,
        "per_core": per_core,
        "frequency": aggregate.frequency_mhz if aggregate else None,
        "physical_cores": static_cores,
        "logical_cores": static_threads,
    }
```

Every converter has the same pattern: check for `Unavailable` and return a well-formed default dict, or extract data from the `MetricsCollection.metrics` list. This keeps the frontend code simple. It never needs to import backend types.

### 4. Bridge Objects

Three bridge classes wrap the same converter functions but offer different execution models:

| Bridge | Paradigm | Used By | Polling |
|--------|----------|---------|---------|
| `SyncBridge` | Synchronous | Textual TUI | Manual `tick_all()` + `get_*()` calls |
| `AsyncBridge` | Asyncio (`run_in_executor`) | Future async apps | `start_polling(interval)` task |
| `EngineBridge` | QObject + QTimer | PyQt6 GUI | `start_polling(interval_ms)` timer |

All three expose the same `get_*()` method family and delegate to the same converter functions.

### 5. Frontend Rendering

Each frontend receives flat dicts and renders them. The TUI uses Textual widgets (Static, DataTable, ProgressBar). The GUI uses PyQt6 widgets and custom chart components.

## Type System

Argus uses a layered type approach. Each layer adds or removes type information.

### Backend Models (caps.py)

Pydantic `BaseModel` classes define the shape of every metric. Each metric carries a timestamp, source tag, and measurement values.

```python
class CPUMetric(BaseModel):
    model_config = ConfigDict(frozen=True)
    usage_percent: float = 0.0
    core_id: int | None = None      # None = aggregate
    frequency_mhz: int | None = None

class MemoryMetric(BaseModel):
    total_bytes: int = 0
    used_bytes: int = 0
    available_bytes: int = 0
    percent: float = 0.0
```

### Collections (caps.py)

`MetricsCollection[T]` is a generic container that bundles a list of metrics with metadata:

```python
class MetricsCollection(BaseModel, Generic[T]):
    metadata: MetricMetadata = MetricMetadata()
    metrics: list[T] = []
```

Type aliases provide convenient shorthand:

```python
CPUMetrics: TypeAlias = MetricsCollection[CPUMetric]
MemoryMetrics: TypeAlias = MetricsCollection[MemoryMetric]
ProcessMetrics: TypeAlias = MetricsCollection[ProcessMetric]
StorageMetrics: TypeAlias = MetricsCollection[StorageMetric]
NetworkMetrics: TypeAlias = MetricsCollection[NetworkMetric]
GPUMetrics: TypeAlias = MetricsCollection[GPUMetric]
SensorMetrics: TypeAlias = MetricsCollection[SensorMetric]
BatteryMetrics: TypeAlias = MetricsCollection[BatteryMetric]
```

### Sentinels (sentinels.py)

`Unavailable` is a frozen dataclass that replaces exceptions for unsupported subsystems.

```python
@dataclass(frozen=True)
class Unavailable:
    reason: str          # "unsupported" | "error" | "timeout" | "disabled"
    detail: str = ""     # human-readable explanation
```

Every tick method returns either a `MetricsCollection[T]` or `Unavailable`. There is no `Optional`. The type is always explicit. This means the caller always knows which subsystems actually produced data and which ones are absent.

### Bridge TypedDicts (engine_bridge.py)

The bridge layer defines `TypedDict` classes for every converter return shape. These serve as documented contracts between the bridge and the frontend.

```python
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
```

The `AggregatedStateDict` TypedDict describes the full state object that `EngineBridge.get_all()` returns:

```python
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
```

### Context TypedDicts (contexts.py)

The hook system defines additional TypedDicts for event payloads. These describe the shape of data that hooks receive during different lifecycle events:

- `CpuTickData` -- `usage_percent`, `per_core`, `physical_cores`, `logical_cores`
- `MemoryTickData` -- `total_bytes`, `used_bytes`, `available_bytes`, `percent`
- `DiskTickData` -- `mount_point`, `total_bytes`, `used_bytes`, `free_bytes`, `percent`
- `NetworkTickData` -- `bytes_sent`, `bytes_recv`, `packets_sent`, `packets_recv`
- `ProcessTickData` -- `pid`, `name`, `cpu_percent`, `memory_rss`, `status`, `username`
- `GpuTickData` -- `name`, `usage_percent`, `memory_total`, `memory_used`
- `BatteryTickData` -- `percent`, `power_plugged`, `seconds_left`
- `SensorTickData` -- `name`, `value`, `unit`
- `GeneralTickData` -- full system state with all subsystems plus `extra: dict[str, object]`

## The Three Bridges

### SyncBridge

Used by the Textual TUI. All calls are synchronous.

```python
bridge = SyncBridge(driver=driver)
bridge.tick_all()                     # refresh from driver
cpu_data = bridge.get_cpu_metrics()   # returns flat dict
```

Key behaviors:
- `tick_all()` calls `driver.tick(DriverContext())` and caches the snapshot.
- Each `get_*()` method reads from the cached snapshot and delegates to a converter.
- `get_all()` calls `tick_all()` then assembles every subsystem into one dict. This is the primary method for the TUI's 2-second refresh cycle.
- `terminate_process(pid)` / `kill_process(pid)` delegate to `driver.manage_process()`.

The TUI creates a `SyncBridge` in `_create_bridge()`:

```python
def _create_bridge():
    from backend.core.engine import BackendEngine
    from backend.bridges.sync_bridge import SyncBridge
    engine = BackendEngine()
    driver = engine.loader.active_driver
    if driver is None:
        raise RuntimeError("No driver loaded")
    return SyncBridge(driver=driver)
```

### AsyncBridge

Intended for asyncio-based consumers (future web or CLI apps). Every `get_*()` method is `async` and runs the blocking driver tick in a thread executor.

```python
bridge = AsyncBridge(driver=driver)
await bridge.start_polling(interval=2.0)
cpu_data = await bridge.get_cpu_metrics()
```

Key behaviors:
- `tick_all()` uses `loop.run_in_executor(None, self._driver.tick, ctx)`.
- `start_polling(interval)` spawns a background task that calls `tick_all()` in a loop.
- `stop_polling()` cancels the background task.
- Each `get_*()` method calls `await tick_all()` first, guaranteeing fresh data.
- `get_all()` does a single async tick and returns all subsystems.

### EngineBridge

Used by the PyQt6 GUI. It is a `QObject` with a `QTimer` for polling and emits a `pyqtSignal` on each tick.

```python
engine = BackendEngine(...)
bridge = EngineBridge(engine)
bridge.state_updated.connect(my_handler)
bridge.start_polling(interval_ms=1000)
```

Key behaviors:
- `_tick()` is the timer callback. It calls `self.get_all()` (which reads from `engine.get_system_state()`), wraps the result in a `BridgeContext`, and emits `state_updated`.
- Individual `get_*()` methods read from `_state` (which calls `engine.get_system_state()`) and extract the relevant subsystem.
- The signal-based design means the GUI never blocks. The timer fires, reads happen on the main thread, and widgets update in response to signals.

## Driver Architecture

### BaseDriver (plugins.py)

`BaseDriver` is an abstract base class that defines the full driver contract. Every driver must implement:

- **Eight per-subsystem tick methods**: `tick_cpu()`, `tick_memory()`, `tick_disk()`, `tick_network()`, `tick_processes()`, `tick_gpu()`, `tick_sensors()`, `tick_battery()`. Each returns `MetricsCollection[T] | Unavailable`.
- **`tick(ctx)`**: The aggregate method. Default implementation calls all eight per-subsystem methods. Drivers can override this for batched collection.
- **`get_static_info()`**: Returns `StaticSystemInfo | None` with hostname, platform, CPU brand, core counts, and RAM.
- **`get_capabilities()`**: Returns `SystemCapabilities` describing which subsystems are available.
- **`manage_process(pid, action)`**: Process management (terminate, kill).

Drivers also get lifecycle hooks:
- `on_load(ctx)` -- called after instantiation.
- `on_unload(ctx)` -- called during disposal.

The default implementation of every tick method returns `Unavailable("unsupported", ...)`. A driver only overrides the methods it supports. This makes platform support incremental.

### Concrete Drivers

- **`generic_linux.py`** -- Collects CPU, memory, disk, network, processes, and sensors via `/proc`, `psutil`, or system calls.
- **`generic_windows.py`** -- Collects the same subsystems via the Windows API (WMI, performance counters, `psutil`).

### DiscoveryLoader (loader.py)

The `DiscoveryLoader` discovers and loads drivers from the `drivers/` directory. It evaluates compatibility via `SystemCapabilities` and selects the best match. The `BackendEngine` wraps the loader and provides the high-level API that bridges consume.

## Hook System (contexts.py)

The hook system provides lifecycle and tick hooks for scripts (Python/Lua) and engine components. Every hook receives a single `ctx` parameter.

### Context Types

**`ScriptContext[T]`** -- For user scripts (Python, Lua). Generic over the payload type.

```python
@dataclass
class ScriptContext(Generic[T]):
    data: T                                    # per-hook payload
    config: ArgusConfig | None = None          # shared config
    db: DatabaseManager | None = None          # shared db
    driver: DriverProxy | BaseDriver | None = None  # active driver
```

A script might use it like this:

```python
def on_tick(ctx: ScriptContext[SystemMetrics]) -> None:
    if ctx.data.cpu and ctx.config:
        ctx.db.write_snapshot(ctx.data)
```

**`DriverContext`** -- Delivered to `BaseDriver.on_tick()` and lifecycle hooks.

```python
@dataclass
class DriverContext:
    data: SystemMetrics | None = None   # latest snapshot (None during init)
    engine: BackendEngine | None = None # engine reference for introspection
```

**`BridgeContext`** -- Delivered to `EngineBridge` signal handlers in the PyQt6 frontend.

```python
@dataclass
class BridgeContext:
    data: dict = field(default_factory=dict)  # aggregate state dict
    bridge: Any | None = None                 # EngineBridge instance
```

A GUI handler receives this type:

```python
def on_state_updated(ctx: BridgeContext) -> None:
    cpu = ctx.data.get("cpu", {})
    update_cpu_bar(cpu.get("cpu_percent", 0.0))
```

## Two Frontends

### Textual TUI (main_tui.py)

A single-file application (~880 lines) that provides 8 screens:

| Key | Screen    | Content |
|-----|-----------|---------|
| 1   | Overview  | Dashboard stat boxes: CPU, RAM, Disk, Processes, Network, Battery |
| 2   | CPU       | Aggregate + per-core usage bars, frequency, temperature |
| 3   | Memory    | RAM breakdown (total / used / free / available) |
| 4   | Disk      | Per-partition usage cards |
| 5   | Network   | Upload/download rates + cumulative totals |
| 6   | Processes | DataTable with search, terminate, kill actions |
| 7   | System    | Static host / platform / CPU / RAM info |
| 8   | About     | Version, keybindings, credits |

Architecture:
- Uses `SyncBridge` directly. Every refresh calls `bridge.get_all()` synchronously.
- Auto-refresh via `set_interval(2.0)` (every 2 seconds). Manual refresh via `r` key.
- Navigation with keys `1`-`8`, quit with `q`.
- Process management: selecting a row and pressing `t` (terminate) or `k` (kill) calls `bridge.terminate_process()` or `bridge.kill_process()`.
- No async code, no PyQt6 dependency. Pure Textual.

### PyQt6 GUI (main_gui.py + frontend/)

The GUI is split into modules:

- **`frontend/core/engine_bridge.py`** -- `EngineBridge` (QObject) with timer-based polling. Emits `state_updated` signal.
- **`frontend/pages/`** -- Page widgets (one per subsystem).
- **`frontend/graphs/`** -- Chart and graph widgets.
- **`frontend/ui/`** -- Shared UI components.
- **`frontend/themes/`** -- Theme definitions.
- **`frontend/assets/`** -- Icons and resources.

Architecture:
- `EngineBridge` owns the polling lifecycle (QTimer). On each tick, it emits `state_updated(BridgeContext)`.
- GUI widgets connect to the signal and update when state changes.
- Individual `get_*()` methods are available for one-shot access without starting the timer.
- Separated converter functions in `backend/bridges/converters.py` are shared with `SyncBridge`. The `EngineBridge` reads raw engine state and applies the same converters.

### Entry Points

| File          | Framework | Bridge       | Use Case |
|---------------|-----------|--------------|----------|
| `main_tui.py` | Textual   | SyncBridge   | Terminal system monitor |
| `main_gui.py` | PyQt6     | EngineBridge | Desktop GUI with charts |
| `main_console.py` | None | (future) | CLI tools, scripts |

## Design Decisions

**Why no `Optional` for subsystem data?** The `Unavailable` sentinel distinguishes "not supported" from "fetch failed" from "not yet collected". A simple `None` collapses all three into one case. The `Unavailable` dataclass carries a reason code (`"unsupported"`, `"error"`, `"timeout"`, `"disabled"`) and an optional detail string. This lets the UI show different messages for each case.

**Why Pydantic models in the backend but plain dicts in the frontend?** Pydantic provides validation, serialization, and type safety for the driver layer. But forcing a UI toolkit to depend on Pydantic creates unnecessary coupling and import overhead. The converter functions in the bridge layer act as an anti-corruption layer, translating between the two worlds.

**Why three bridges instead of one?** Each UI paradigm has different execution requirements. Textual is synchronous and single-threaded. Future async apps need non-blocking I/O. PyQt6 needs signal-based communication with the Qt event loop. One bridge with conditional branches would be harder to test and maintain. Three separate classes, each with a clear contract, is simpler.

**Why a separate converter module?** The converter functions are pure transformations with no side effects. They are trivially testable. They have no dependencies on any UI framework. Both `SyncBridge` and `EngineBridge` import and call the same functions, ensuring consistent output between the TUI and GUI.
