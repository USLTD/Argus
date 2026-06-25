# Argus TUI User Guide

The Textual TUI provides a keyboard-driven system monitor in your terminal. It uses a dark theme with teal backgrounds and a red accent color, and refreshes all metrics automatically.

## Launching

From the project root:

```bash
python main_tui.py
```

**Requirements:**
- Python 3.10+
- The `textual` package (included in project dependencies)
- A working backend driver (auto-detected by `BackendEngine`)

On startup the application creates a `SyncBridge` connected to the active system driver, then shows the Overview screen.

## Screens Overview

There are 8 screens, switchable with the number keys `1` through `8`. The active screen is shown in the header bar.

| Key | Screen | Description |
|-----|--------|-------------|
| `1` | **Overview** | Dashboard with stat boxes for CPU, RAM, Disk, and Processes, plus Network and Battery cards |
| `2` | **CPU** | Aggregate usage bar, per-core bars, frequency display, and temperature sensors |
| `3` | **Memory** | RAM usage bar with breakdown: total, used, available, free |
| `4` | **Disk** | Per-partition or per-mount-point usage cards with progress bars |
| `5` | **Network** | Upload and download rates with cumulative byte totals |
| `6` | **Processes** | DataTable of all processes (PID, Name, CPU%, Memory, Status). Search filter input and Terminate/Kill buttons |
| `7` | **System** | Static system info: hostname, OS, platform version, CPU brand, cores, RAM, boot time |
| `8` | **About** | App version, key binding reference, and credits |

## Navigation

The header and footer show available actions. All navigation is keyboard-based.

| Key | Action |
|-----|--------|
| `1` | Switch to Overview screen |
| `2` | Switch to CPU screen |
| `3` | Switch to Memory screen |
| `4` | Switch to Disk screen |
| `5` | Switch to Network screen |
| `6` | Switch to Processes screen |
| `7` | Switch to System screen |
| `8` | Switch to About screen |
| `r` | Force-refresh the current screen immediately |
| `q` or `Ctrl+C` | Quit the application |

Each screen switch calls `push_screen`, which adds the new screen to the navigation stack. The About screen provides an additional `ESC` binding to pop back to the previous screen.

## Auto-Refresh

Every screen automatically refreshes its data on a **2-second interval**. The refresh cycle:

1. Calls `bridge.tick_all()` to pull fresh data from the system driver.
2. Reads specific metrics from the bridge for the current screen.
3. Updates all widgets (stat labels, progress bars, tables, etc.).

You can also press **`r`** at any time to trigger an immediate refresh. This calls `tick_all()` followed by the current screen's `_poll()` method, even between regular interval ticks.

On error (e.g. a bridge call fails), the poll is silently skipped so the UI never crashes from a transient data source failure.

## Process Management (Screen 6)

The Processes screen provides an interactive process list.

### Search

Type in the search **Input** widget at the top of the screen. The process list filters in real-time to show only entries whose name or PID matches the search string. Matching is case-insensitive and checks the process name field only.

### Sorting

Processes are sorted by CPU usage in descending order (highest CPU% first). The list is capped at **200 processes** to keep the UI responsive.

### Terminate / Kill

The **Terminate** and **Kill** buttons sit below the DataTable.

1. Click or navigate to a process row in the DataTable to select it.
2. Press **Terminate** to send `SIGTERM` a graceful shutdown signal.
3. Press **Kill** to send `SIGKILL` a forceful immediate kill.

Both buttons call `bridge.terminate_process(pid)` or `bridge.kill_process(pid)` respectively. The buttons remain functional regardless of selection state but will silently do nothing if no valid row is selected.

## Data Sources

The `SyncBridge` object (accessible as `app.bridge`) provides all system metrics. Each screen reads from specific bridge methods:

| Screen | Bridge method(s) |
|--------|-----------------|
| Overview | `get_all()`, `get_cpu_metrics()`, `get_memory_metrics()`, `get_disk_usage(mount)`, `get_process_list()`, `get_network_io()`, `get_battery()` |
| CPU | `get_cpu_metrics()`, `get_sensors()` |
| Memory | `get_memory_metrics()` |
| Disk | `get_disk_usage(mount_point)` per partition |
| Network | `get_network_io()` |
| Processes | `get_process_list()` |
| System | `get_static_info()`, `get_boot_time()` |
| About | (no bridge calls) |

### Mount Discovery

The TUI discovers mount points through `_discover_mounts()`:

- **Windows**: Iterates drive letters A through Z, returning paths like `C:\` for each existing drive.
- **Linux / macOS**: Returns `["/"]` (root mount only).

The Disk screen uses this list to build one info card per mount point. Cards are mounted once on first poll, then updated each interval.

## Formatting Helpers

The TUI uses several internal functions to format raw values into human-readable text. These are defined at module scope in `main_tui.py` and used by all screens.

### `_fmt_bytes(n)`

Converts a byte count to a human-readable string with the appropriate unit.

| Input | Output |
|-------|--------|
| `512` | `512.0 B` |
| `8192` | `8.0 KB` |
| `8388608` | `8.0 MB` |
| `8589934592` | `8.0 GB` |

Walls at PB for extremely large values.

### `_fmt_speed(bps)`

Converts bytes per second to a human-readable speed string. Delegates to `_fmt_bytes` with `B/s` appended.

| Input | Output |
|-------|--------|
| `0.5` | `0 B/s` |
| `45_000_000` | `45.0 MB/s` |
| `1_200_000_000` | `1.2 GB/s` |

### `_fmt_freq(mhz)`

Formats CPU frequency in MHz. Values at or above 1000 MHz are displayed in GHz.

| Input | Output |
|-------|--------|
| `None` | `N/A` |
| `800` | `800 MHz` |
| `2400` | `2.40 GHz` |

### `_fmt_seconds(secs)`

Converts a duration in seconds to a short human format. Returns `N/A` for `None` or zero values.

| Input | Output |
|-------|--------|
| `None` | `N/A` |
| `2700` | `45m` |
| `9000` | `2h 30m` |

## Appearance

The TUI uses a custom dark theme defined as inline CSS:

- **Background**: `#1a1a2e` (deep navy)
- **Header / Footer**: `#16213e` with text in accent red (`#e94560`)
- **Stat boxes and cards**: solid border in `#0f3460`, background `#16213e`
- **Stat values**: green (`#00ff88`) for emphasis
- **Progress bars**: red foreground on dark blue background
- **DataTable cursor**: red background with dark text
- **Buttons**: dark blue resting state, red on hover/focus

## Architecture Notes

The TUI is built with:

- **Textual** for the terminal UI framework (App, Screen, widgets).
- **BackendEngine** and **SyncBridge** for data collection via the active system driver.
- **psutil** (indirectly, through the backend) for system metrics.
- **Pydantic** for data models in the backend.

The `ArgusTUI` application class registers all 8 screens in its `SCREENS` dictionary and starts on the Overview screen. Each screen is a subclass of `textual.screen.Screen` with its own `compose()` layout, `on_mount()` interval setup, and `_poll()` data update method.
