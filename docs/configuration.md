# Configuration

Argus uses **pydantic-settings** to manage configuration, backed by a YAML file with optional environment variable overrides.

## Config File Location

The config file path is resolved by `resolve_config_path()` in `backend/core/paths.py`:

1. **`ARGUS_CONFIG_PATH`** environment variable (if set) — explicit path
2. **Platform-specific default**:
   - **Linux**: `~/.config/argus/config.yml`
   - **Windows**: `%APPDATA%/Argus/config.yml`
   - **macOS**: `~/Library/Application Support/Argus/config.yml`

The config file is **auto-created with defaults** on first run if it doesn't exist.

## Environment Variable Overrides

Every config field can be overridden at runtime via environment variables with the `ARGUS_` prefix:

```bash
ARGUS_THEME=nord ARGUS_POLL_INTERVAL_MS=500 python main_tui.py
```

Environment variables take precedence over values in the YAML file.

## All Config Options

| Field | Type | Default | Env Var | Description |
|---|---|---|---|---|
| `driver_override` | `str \| None` | `None` | `ARGUS_DRIVER_OVERRIDE` | Force a specific driver by name (e.g. `"generic_linux"`). Auto-detected when `None`. |
| `poll_interval_ms` | `int` | `1000` | `ARGUS_POLL_INTERVAL_MS` | Milliseconds between engine ticks. All subsystems refresh at this rate. |
| `script_compatibility_default` | `str` | `"skip"` | `ARGUS_SCRIPT_COMPATIBILITY_DEFAULT` | Default action for scripts without explicit compatibility: `"load"` or `"skip"`. |
| `script_batch_size` | `int` | `4` | `ARGUS_SCRIPT_BATCH_SIZE` | Maximum number of scripts that can execute concurrently in the thread pool. |
| `script_timeout_ms` | `int` | `5000` | `ARGUS_SCRIPT_TIMEOUT_MS` | Maximum execution time per script in milliseconds. Scripts exceeding this are cancelled. |
| `script_execution_mode` | `str` | `"nonblocking"` | `ARGUS_SCRIPT_EXECUTION_MODE` | Default execution mode for scripts: `"blocking"`, `"nonblocking"`, or `"mixed"`. |
| `process_tick_interval` | `int` | `5` | `ARGUS_PROCESS_TICK_INTERVAL` | Collect process list every N ticks (default 5 = ~5s at 1s poll). Saves CPU on busy systems. |

### Script Execution Modes

| Mode | Behavior |
|---|---|
| `"blocking"` | Script runs synchronously in the tick loop. Engine waits for completion before proceeding. |
| `"nonblocking"` | Script runs in the thread pool. Engine continues ticking; output collected asynchronously. |
| `"mixed"` | Script runs in the thread pool, but engine waits up to `script_timeout_ms` for completion if any blocking scripts are queued. |

### process_tick_interval Details

The `process_tick_interval` field controls how often the (potentially expensive) process list scan runs. On skipped ticks, the engine reuses the last cached process snapshot. This reduces CPU overhead on systems with many processes.

- **`1`** = collect processes every tick (same as pre-configurable behavior)
- **`5`** = collect processes every 5th tick (~5 seconds at default 1s poll)
- **`10`** = collect every 10th tick (~10s)

Process CPU usage percentages and memory data for **other subsystems** (CPU, memory, disk, network, GPU) are unaffected — they still refresh every tick.

## Example Config File

```yaml
poll_interval_ms: 2000
script_batch_size: 8
script_timeout_ms: 10000
script_execution_mode: mixed
process_tick_interval: 3
```

## Unknown Environment Variables

Unknown `ARGUS_*` environment variables are captured via `model_extra` (the `ArgusConfig` model has `extra="allow"`) and are persisted to YAML on save. This means any unrecognized `ARGUS_*` variable set at runtime will be preserved in the config file.

## Adding New Config Options

New config fields follow this pattern:

1. Add a field to the `ArgusConfig` class in `backend/storage/config.py`
2. The field name is automatically kebab-cased for YAML and `UPPER_CASE` for env vars (via `ARGUS_` prefix)
3. Document the field in this file
