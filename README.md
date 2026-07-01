# Argus

**Cross-platform system monitor and process manager** written in Python. Two frontends -- a full-featured **PyQt6 GUI** and a keyboard-driven **Textual TUI** -- both backed by a common driver-based metric collection engine with a plugin architecture, scripting hooks, and Lua/Python script support.

## Quick Start

```bash
uv sync
uv run main_console.py # launch basic CLI
uv run main_tui.py     # launch Textual TUI
uv run main_gui.py     # launch PyQt6 GUI (requires PyQt6)
```

## Architecture

Argus follows a clean three-layer architecture: drivers collect raw system data, bridges convert it to flat dicts, and frontends render it.

```
                     ┌──────────────────────┐
                     │     BaseDriver        │
                     │   tick(ctx) returns   │
                     │    TickSnapshot       │
                     └──────────┬───────────┘
                                │
                                ▼
                     ┌──────────────────────┐
                     │   MetricsCollection  │
                     │   [T] | Unavailable  │
                     └──────────┬───────────┘
                                │
            ┌───────────────────┼───────────────────┐
            ▼                   ▼                   ▼
  ┌──────────────────┐ ┌────────────────┐ ┌──────────────────┐
  │   AsyncBridge     │ │  SyncBridge   │ │  EngineBridge    │
  │ async, asyncio    │ │ sync, no deps │ │ QTimer, pyqtSigs │
  │ used by Textual   │ │ CLI/scripts   │ │ used by PyQt6    │
  └────────┬─────────┘ └───────┬────────┘ └────────┬─────────┘
           │                   │                    │
           ▼                   ▼                    ▼
  ┌────────────────┐  ┌──────────────┐  ┌──────────────────────┐
  │   main_tui.py  │  │  CLI/scripts │  │    main_gui.py       │
  │   (Textual)    │  │              │  │    frontend/pages/   │
  └────────────────┘  └──────────────┘  └──────────────────────┘
```

### Data Flow

1. **Drivers** implement `BaseDriver` with typed tick methods (`tick_cpu()`, `tick_memory()`, etc.), each returning `MetricsCollection[T]` or `Unavailable`.
2. **BackendEngine** orchestrates driver lifecycle: discovery, loading, compatibility scoring, and tick dispatch.
3. **Bridges** wrap the driver, call `tick_all()`, and convert typed collections to plain dicts via `converters.py`.
4. **Frontends** read dict-shaped data and render it -- either a Textual TUI (`main_tui.py`) or PyQt6 GUI (`main_gui.py`).

The hook system (in `contexts.py`) lets scripts and plugins intercept lifecycle events, tick data, and signals without modifying core code.

## Features

- **9 TUI screens**: Overview, CPU, Memory, Disk, Network, Processes, System, About, Settings -- switch with `1`-`9`
- **PyQt6 GUI**: Full graphical interface with real-time charts, process management, and detail pages
- **Cross-platform**: Linux (`generic_linux.py`) and Windows (`generic_windows.py`) drivers ship built-in
- **Plugin driver architecture**: Drop-in drivers with auto-discovery and compatibility scoring
- **Process management**: Search by name, terminate (SIGTERM), kill (SIGKILL) from the Processes screen
- **2-second auto-refresh**: All screens refresh on a configurable polling interval
- **Hook system**: Lifecycle hooks, tick hooks, and signal hooks for extensibility
- **Scripting**: Python and Lua scripts (`scripts/`) that run on driver ticks -- CPU logging, disk watchdogs, sensor dashboards, network monitors, and more
- **Sandboxed Lua**: Lua scripts run via `lupa` with an isolated sandbox environment
- **Three bridge APIs**: `SyncBridge` (synchronous, used by CLI/scripts), `AsyncBridge` (asyncio, used by TUI), `EngineBridge` (PyQt6 `QObject` with signals) -- all exposing the same `get_*()` interface

## Requirements

- Python 3.14+
- [Textual](https://github.com/Textualize/textual) >= 8.2.7 (TUI)
- [pydantic](https://github.com/pydantic/pydantic) >= 2.14
- [lupa](https://github.com/scoder/lupa) >= 2.8 (Lua scripting runtime)
- PyQt6 >= 6.8.0 + pyqtgraph >= 0.13.7 (GUI, optional)

Managed via `uv` with dependency groups:
- `dev` -- test and development tooling
- `cli` -- Rich library for console output
- `tui` -- Textual library (TUI)
- `gui` -- PyQt6 + pyqtgraph (GUI, optional)
- `driver-win` -- Windows driver extras (WMI, pywin32)
- `driver-linux` -- Linux driver extras (GPUtil)
- `drivers-common` -- psutil (shared by all drivers)

## Project Structure

```
argus/
├── backend/
│   ├── bridges/           # Data-access layers (converters, SyncBridge, AsyncBridge)
│   │   ├── converters.py  # MetricsCollection[T] -> flat dicts
│   │   ├── sync_bridge.py # Synchronous driver bridge (used by CLI/scripts)
│   │   └── async_bridge.py# Async driver bridge (used by TUI)
│   ├── core/              # Engine, driver loader, scripting runtime, sandbox
│   │   ├── engine.py      # BackendEngine -- tick orchestrator
│   │   ├── loader.py      # DiscoveryLoader -- driver discovery & scoring
│   │   ├── driver_proxy.py# Proxy layer around active driver
│   │   ├── python_script.py# Python script wrapper
│   │   ├── sandbox.py     # Lua sandboxed runtime
│   │   └── injectors/     # Script dependency injection
│   ├── interfaces/        # Base classes, capability models, sentinels, hooks
│   │   ├── plugins.py     # BaseDriver, BasePlugin, PluginMeta
│   │   ├── caps.py        # MetricsCollection[T], CPUMetric, MemoryMetric, etc.
│   │   ├── contexts.py    # Hook context types (ScriptContext, DriverContext, BridgeContext)
│   │   ├── sentinels.py   # TickSnapshot, Unavailable types
│   │   ├── enums.py       # Permission, ConfidenceScore, CompatAction
│   │   ├── permissions.py # PermissionHierarchy
│   │   └── rules.py       # Compatibility evaluation rules
│   └── storage/           # Configuration and database
│       ├── config.py      # ArgusConfig (pydantic-settings)
│       └── database.py    # DatabaseManager
├── frontend/
│   ├── core/              # PyQt6 app services + backwards-compat re-exports
│   ├── pages/             # GUI page widgets (CPU, Memory, Disk, etc.)
│   ├── ui/                # GUI toolbar, dialog, widget components
│   └── graphs/            # GUI chart widgets
├── drivers/
│   ├── builtin/           # Shipping drivers
│   │   ├── generic_linux.py   # Linux driver using psutil + /proc
│   │   └── generic_windows.py # Windows driver using psutil + WMI
│   └── custom/            # User-provided drivers (auto-discovered)
├── scripts/               # Python and Lua user scripts
│   ├── cpu_logger.py      # Example: log CPU metrics
│   ├── disk_watchdog.lua  # Example: alert on disk usage
│   ├── memory_logger.lua  # Example: log memory metrics
│   ├── process_watchdog.lua # Example: monitor processes
│   └── ...                # (8 more scripts in repo)
├── docs/                  # Documentation
├── main_tui.py            # Textual TUI entry point (884 lines)
├── main_gui.py            # PyQt6 GUI entry point
├── main_console.py        # Console/debug entry point
└── pyproject.toml         # Project metadata & dependencies
```

## Screens

### TUI (Textual)

| Key | Screen   | Contents |
|-----|----------|----------|
| `1` | Overview | Dashboard stat boxes (CPU, RAM, Disk, Processes) + Network + Battery |
| `2` | CPU      | Aggregate + per-core usage bars, frequency, temperature |
| `3` | Memory   | RAM breakdown (total / used / free / available) |
| `4` | Disk     | Per-partition usage cards |
| `5` | Network  | Upload/download rates + cumulative totals |
| `6` | Processes| DataTable with search, terminate, kill |
| `7` | System   | Static host/platform/CPU/RAM info |
| `8` | About    | Version, keybindings, credits |
| `9` | Settings | Live config editing (theme, polling, scripting parameters) |

Navigation: `1`-`9` to switch screens, `q` / `Ctrl+C` to quit, `r` to force-refresh.

## Scripting

Argus ships a hook-based scripting engine. Python and Lua scripts in `scripts/` are loaded at startup and receive tick data through lifecycle hooks:

- `on_tick(ctx: ScriptContext[SystemMetrics])` -- called every tick
- `on_start(ctx: ScriptContext[None])` -- on engine start
- `on_stop(ctx: ScriptContext[None])` -- on engine stop
- `on_config_change(ctx: ScriptContext[dict])` -- on config reload

Lua scripts run in a sandboxed environment with controlled access to Argus types, config, and database.

## Extending

### Writing a Driver

Implement `BaseDriver` from `backend/interfaces/plugins.py`:

```python
from backend.interfaces.plugins import BaseDriver
from backend.interfaces.caps import CPUMetric, MetricsCollection, StaticSystemInfo
from backend.interfaces.contexts import DriverContext

class MyDriver(BaseDriver):
    def tick_cpu(self, ctx: DriverContext) -> MetricsCollection[CPUMetric]:
        # collect CPU data...
        ...

    def get_static_info(self) -> StaticSystemInfo:
        ...
```

Drop the driver into `drivers/custom/` and the `DiscoveryLoader` finds it automatically, scoring it against the host system's capabilities.

## License

MIT
