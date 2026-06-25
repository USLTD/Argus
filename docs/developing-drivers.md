# Developing Argus Drivers

Argus uses a plugin-style driver architecture to collect system metrics. Each
driver is a Python class that subclasses `BaseDriver`, implements 8
per-subsystem tick methods, and exposes static system info. The
`DiscoveryLoader` scans well-known directories, evaluates compatibility, and
activates the best match at startup.

## Driver Interface

### BaseDriver

Every driver inherits from `BaseDriver` (defined in
`backend/interfaces/plugins.py`):

```python
from backend.interfaces.plugins import BaseDriver
from backend.interfaces.contexts import DriverContext
from backend.interfaces.sentinels import TickSnapshot

class MyDriver(BaseDriver):
    def tick(self, ctx: DriverContext) -> TickSnapshot:
        ...
```

### Required Tick Methods

Each of the eight subsystems has a dedicated method. Every method receives a
`DriverContext` and returns `MetricsCollection[T] | Unavailable`. Return
`Unavailable` when your driver does not support that subsystem.

| Method | Return Type | Description |
|--------|-------------|-------------|
| `tick_cpu(ctx)` | `MetricsCollection[CPUMetric]` | Per-core CPU usage and frequency |
| `tick_memory(ctx)` | `MetricsCollection[MemoryMetric]` | RAM total, used, available, percent |
| `tick_disk(ctx)` | `MetricsCollection[StorageMetric]` | Per-mount-point disk usage |
| `tick_network(ctx)` | `MetricsCollection[NetworkMetric]` | Per-interface network I/O counters |
| `tick_processes(ctx)` | `MetricsCollection[ProcessMetric]` | Snapshot of running processes |
| `tick_sensors(ctx)` | `MetricsCollection[SensorMetric]` | Temperature, voltage, fan sensors |
| `tick_battery(ctx)` | `MetricsCollection[BatteryMetric]` | Battery charge level and status |
| `tick_gpu(ctx)` | `MetricsCollection[GPUMetric]` | Per-GPU usage and memory |

The base class provides a default `tick()` that calls all eight in sequence
and bundles them into a `TickSnapshot`. Override `tick()` only if you need
batching or custom orchestration.

### Metric Types

All metric models are Pydantic `BaseModel` subclasses from
`backend/interfaces/caps.py`:

```python
class CPUMetric(BaseModel):
    core_id: int | None = None
    usage_percent: float = 0.0
    frequency_mhz: float | None = None

class MemoryMetric(BaseModel):
    total_bytes: int = 0
    used_bytes: int = 0
    available_bytes: int = 0
    percent: float = 0.0

class ProcessMetric(BaseModel):
    pid: int = 0
    name: str = ""
    cpu_percent: float = 0.0
    memory_rss: int = 0
    status: str = ""
    username: str | None = None

class StorageMetric(BaseModel):
    mount_point: str = ""
    total_bytes: int = 0
    used_bytes: int = 0
    free_bytes: int = 0
    percent: float = 0.0

class GPUMetric(BaseModel):
    name: str = ""
    usage_percent: float = 0.0
    memory_total: int = 0
    memory_used: int = 0

class NetworkMetric(BaseModel):
    bytes_sent: int = 0
    bytes_recv: int = 0
    packets_sent: int = 0
    packets_recv: int = 0

class SensorMetric(BaseModel):
    name: str = ""
    value: float = 0.0
    unit: str = "celsius"

class BatteryMetric(BaseModel):
    percent: float = 0.0
    power_plugged: bool | None = None
    seconds_left: float | None = None
```

Each method returns a `MetricsCollection[T]`:

```python
class MetricsCollection(BaseModel, Generic[T]):
    metadata: MetricMetadata = MetricMetadata()
    metrics: list[T] = []

class MetricMetadata(BaseModel):
    collected_at: float = 0.0    # time.time() timestamp
    source: str = "driver"       # source label
    hostname: str = ""           # originating host
```

### Unavailable Sentinel

When a subsystem cannot produce data, return `Unavailable` (imported from
`backend/interfaces/sentinels`). This is a frozen dataclass with two fields:

```python
@dataclass(frozen=True)
class Unavailable:
    reason: str    # "unsupported" | "error" | "timeout" | "disabled"
    detail: str = ""  # human-readable explanation
```

Use the reason codes consistently:

- `"unsupported"` -- capability absent (no GPU on this system)
- `"error"` -- the fetch call raised an exception
- `"timeout"` -- the fetch timed out
- `"disabled"` -- explicitly disabled by configuration

### Static System Info

Override `get_static_info()` to return a `StaticSystemInfo` instance with
hardware and OS metadata:

```python
from backend.interfaces.caps import StaticSystemInfo

def get_static_info(self) -> StaticSystemInfo | None:
    return StaticSystemInfo(
        os_name="Linux",
        os_version="6.1.0",
        hostname="my-box",
        username="user",
        cpu_brand="Intel Core i7",
        cpu_physical_cores=4,
        cpu_logical_cores=8,
        cpu_frequency_mhz=2400.0,
        gpu_name="NVIDIA GeForce RTX 3060",
        gpu_driver="NVIDIA 535.154.05",
        gpu_vram_bytes=8589934592,
        motherboard_manufacturer="ASUS",
        motherboard_model="ROG STRIX B550-F",
        bios_version="2803",
        total_ram_bytes=17179869184,
        architecture="x86_64",
        python_version="3.11.0",
        boot_time="2025-01-01 00:00:00",
    )
```

The default returns `None`. Return `None` if static info is unavailable.

### Process Management

Implement `manage_process()` to handle process control actions:

```python
from typing import Any

def manage_process(self, pid: int, action: str, **kwargs: Any) -> bool:
    if action == "terminate":
        # send SIGTERM
    elif action == "kill":
        # send SIGKILL
    elif action == "suspend":
        # send SIGSTOP
    elif action == "resume":
        # send SIGCONT
    else:
        return False
    return True
```

Return `True` on success, `False` if the action is not supported or fails.

### Capabilities

Drivers must declare their capabilities via `get_capabilities()`. This returns
a `SystemCapabilities` instance that tells the engine which subsystems the
driver supports:

```python
from backend.interfaces.caps import SystemCapabilities

def get_capabilities(self) -> SystemCapabilities:
    return SystemCapabilities(
        has_process_list=True,
        has_gpu=False,
        has_storage=True,
        has_network=True,
        has_sensors=True,
        has_battery=True,
    )
```

You can also populate the detailed sub-models (`CpuCapabilities`,
`ProcessCapabilities`, `DriverInfo`, etc.) for finer-grained reporting.

### Lifecycle Hooks

`BaseDriver` provides two optional lifecycle hooks:

```python
def on_load(self, ctx: DriverContext | None = None) -> None:
    """Called after instantiation. Set up resources, open connections."""

def on_unload(self, ctx: DriverContext | None = None) -> None:
    """Called during disposal. Release resources, close connections."""
```

The base `__init__` calls `on_load()` automatically, so you do not need to
call it yourself. Override `on_unload()` to clean up file handles, subprocesses,
or network connections when the driver is swapped or the engine shuts down.

## Module-Level Exports

The `DiscoveryLoader` expects two module-level names in every driver file:

### METADATA

A `PluginMeta` dictionary describing the driver:

```python
from backend.interfaces.plugins import PluginMeta
from backend.interfaces.plugins import PluginMeta

METADATA: PluginMeta = {
    "name": "My Custom Driver",
    "author": "Your Name",
    "version": "1.0.0",
    "compatible": [
        "sys.platform EQ 'linux' -> HIGH",
    ],
}
```

The `compatible` field is a list of DSL rules that the engine evaluates at
load time. Each rule maps platform conditions to a `ConfidenceScore` level.
The driver with the highest confidence score wins.

You can also use a callable:

```python
from backend.interfaces.enums import ConfidenceScore

METADATA: PluginMeta = {
    ...
    "compatible": lambda ctx: ConfidenceScore.FULL,
}
```

### DRIVER

A reference to the driver class itself:

```python
class MyDriver(BaseDriver):
    ...

DRIVER = MyDriver
```

## Example: Minimal Driver

Here is a complete, minimal driver that collects CPU usage via `psutil` and
marks everything else as unsupported:

```python
from typing import Any, override

from backend.interfaces.caps import (
    CPUMetric,
    MemoryMetric,
    MetricsCollection,
    StaticSystemInfo,
    SystemCapabilities,
)
from backend.interfaces.contexts import DriverContext
from backend.interfaces.enums import ConfidenceScore
from backend.interfaces.plugins import BaseDriver, PluginMeta
from backend.interfaces.sentinels import Unavailable


METADATA: PluginMeta = {
    "name": "Minimal Driver",
    "author": "Example",
    "version": "0.1.0",
    "compatible": lambda ctx: ConfidenceScore.MEDIUM,
}


class MinimalDriver(BaseDriver):
    @override
    def get_capabilities(self) -> SystemCapabilities:
        return SystemCapabilities(
            has_process_list=False,
            has_gpu=False,
            has_storage=False,
            has_network=False,
            has_sensors=False,
            has_battery=False,
        )

    @override
    def tick_cpu(self, ctx: DriverContext) -> MetricsCollection[CPUMetric] | Unavailable:
        import time
        import psutil

        return MetricsCollection[CPUMetric](
            metadata=MetricMetadata(collected_at=time.time()),
            metrics=[CPUMetric(usage_percent=psutil.cpu_percent(interval=0))],
        )

    # Everything else is unsupported
    @override
    def tick_memory(self, ctx: DriverContext) -> MetricsCollection[MemoryMetric] | Unavailable:
        return Unavailable("unsupported", "Memory monitoring not implemented")

    @override
    def tick_disk(self, ctx: DriverContext) -> Unavailable:
        return Unavailable("unsupported", "Disk monitoring not implemented")

    @override
    def tick_network(self, ctx: DriverContext) -> Unavailable:
        return Unavailable("unsupported", "Network monitoring not implemented")

    @override
    def tick_processes(self, ctx: DriverContext) -> Unavailable:
        return Unavailable("unsupported", "Process listing not implemented")

    @override
    def tick_gpu(self, ctx: DriverContext) -> Unavailable:
        return Unavailable("unsupported", "GPU monitoring not implemented")

    @override
    def tick_sensors(self, ctx: DriverContext) -> Unavailable:
        return Unavailable("unsupported", "Sensor monitoring not implemented")

    @override
    def tick_battery(self, ctx: DriverContext) -> Unavailable:
        return Unavailable("unsupported", "Battery monitoring not implemented")

    @override
    def get_static_info(self) -> StaticSystemInfo | None:
        import platform

        return StaticSystemInfo(
            os_name=platform.system(),
            os_version=platform.version(),
            hostname=platform.node(),
            username="",
            cpu_brand="",
            cpu_physical_cores=0,
            cpu_logical_cores=0,
            total_ram_bytes=0,
            architecture=platform.machine(),
            python_version=platform.python_version(),
            boot_time="",
        )

    @override
    def manage_process(self, pid: int, action: str, **kwargs: Any) -> bool:
        return False


DRIVER = MinimalDriver
```

## Registering a Driver

### Automatic Discovery

The `DiscoveryLoader` (in `backend/core/loader.py`) scans two directories at
startup:

| Directory | Purpose |
|-----------|---------|
| `drivers/builtin/` | First-party drivers shipped with Argus |
| `drivers/custom/` | Third-party or user-written drivers |

Place your `.py` file in either directory. The loader will:

1. Import the module dynamically.
2. Look for a `DRIVER` attribute holding a `BaseDriver` subclass.
3. Read the `METADATA` dictionary for name, version, permissions, and
   compatibility rules.
4. Evaluate compatibility against the current system context.
5. Activate the driver with the highest `ConfidenceScore`.

If no compatible driver is found, the engine falls back to an
error-producing snapshot.

### Manual Instantiation

You can bypass discovery and set a driver directly:

```python
from backend.core.engine import BackendEngine

engine = BackendEngine()
engine.loader.active_driver = MyDriver()
```

## Reference Implementations

### FakeDriver (testing)

`tests/fake_driver.py` returns deterministic, static data for every subsystem.
It is the simplest reference implementation and a good template when you want
to see every method wired up at once. Key characteristics:

- Returns fixed CPU (42.5%), memory (50%), processes, GPU, sensors, battery.
- Returns `Unavailable("unsupported", ...)` for disk and network.
- `manage_process` only supports the `"kill"` action.
- Declares compatibility as `lambda ctx: ConfidenceScore.FULL` so it always
  passes compatibility checks in tests.

Use it as a scaffolding starting point: replace each static return with a real
collection call one subsystem at a time.

### generic_linux.py

`drivers/builtin/generic_linux.py` is the production Linux driver. It uses
`psutil` for CPU, memory, disk, network, processes, sensors, and battery.
GPU metrics come from the optional `GPUtil` library. Key patterns it
demonstrates:

- Wrapping each call in `try/except` and returning `Unavailable("error", str(e))`
  on failure.
- Using `MetricMetadata(collected_at=time.time())` to timestamp each collection.
- Building per-core CPU metrics alongside an aggregate.
- Gracefully degrading when an optional dependency (`GPUtil`) is missing.
- Declaring platform-specific compatibility via the DSL:
  ```python
  "compatible": ["sys.platform EQ 'linux' -> HIGH"]
  ```

### generic_windows.py

`drivers/builtin/generic_windows.py` mirrors `generic_linux.py` but targets
Windows. It uses `psutil` for most metrics and WMI queries for Windows-specific
data such as GPU info (via `wmi` + `pywin32`). Its compatibility rule is:

```python
"compatible": ["sys.platform EQ 'win32' -> HIGH"]
```

## Testing Your Driver

### Using the FakeDriver as a Base

Subclass `FakeDriver` to get a working test harness with static data. Override
only the methods you need to change:

```python
from tests.fake_driver import FakeDriver

class MyTestDriver(FakeDriver):
    def tick_cpu(self, ctx):
        # replace with real implementation
        ...
```

### Manual Tick via SyncBridge

For quick iteration, instantiate your driver with the engine and call tick
methods directly:

```python
from backend.core.engine import BackendEngine
from backend.interfaces.contexts import DriverContext

engine = BackendEngine()
engine.loader.active_driver = MyDriver()
ctx = DriverContext()

snapshot = engine.tick()
print(snapshot.cpu)
```

### Running the Test Suite

Run the full test suite to verify nothing is broken:

```bash
uv run -- python -m pytest -q
```

Run a specific test file:

```bash
uv run -- python -m pytest tests/test_smoke.py -q
```

## Checklist

Before submitting your driver, verify:

- [ ] Class inherits from `BaseDriver`.
- [ ] All eight tick methods are implemented (return `Unavailable` for
      unsupported subsystems).
- [ ] `get_capabilities()` returns an accurate `SystemCapabilities` instance.
- [ ] `manage_process()` handles at least the no-op case.
- [ ] `METADATA` and `DRIVER` are exported at module level.
- [ ] Compatibility rules or callable are set in `METADATA`.
- [ ] `on_unload()` cleans up any resources (file handles, threads,
      connections).
- [ ] Driver file is placed in `drivers/builtin/` or `drivers/custom/`.
- [ ] Tests pass with `uv run -- python -m pytest -q`.
