# Lua Scripting

## Overview

Lua scripts are `.lua` files dropped into the `scripts/` directory, discovered
and loaded alongside Python scripts by the same engine machinery. They run in
a sandboxed `lupa` runtime with controlled access to system resources.

Script loading is a two-phase process:

1. **Phase 1** -- A bare `LuaRuntime` evaluates the script to extract
   `METADATA` and check compatibility rules. No sandbox is applied yet.
2. **Phase 2** -- If compatible, a fresh sandboxed runtime loads the script,
   injects the `argus` namespace, executes the source, then removes dangerous
   globals.

## Hook API

Lua scripts register callbacks by assigning functions to slots on the
`argus` table. The engine captures these assignments after execution.

### Lifecycle hooks

```lua
function argus.lifecycle.on_load(ctx)
    print("Script loaded")
end

function argus.lifecycle.on_unload(ctx)
    print("Script unloaded")
end
```

### Subsystem event hooks

Assign a function to the `on_tick` slot of any subsystem namespace:

```lua
-- General tick (full system state)
argus.events.general.on_tick = function(ctx)
    local cpu = ctx["data"]["cpu"]
    print("CPU: " .. cpu["usage_percent"] .. "%")
end

-- CPU-specific tick
argus.events.cpu.on_tick = function(ctx)
    local data = ctx["data"]
    print("CPU: " .. data["usage_percent"] .. "%")
end

-- Disk volumes tick
argus.events.disk.on_tick = function(ctx)
    for _, vol in ipairs(ctx["data"]) do
        print(vol["mount_point"] .. " " .. vol["percent"] .. "%")
    end
end
```

Available subsystem events:

| Event path                          | Payload type                  | Required permission |
|-------------------------------------|-------------------------------|---------------------|
| `argus.events.general.on_tick`      | `GeneralTickData`             | `SCRIPT.READ`       |
| `argus.events.cpu.on_tick`          | `CpuTickData`                 | `SCRIPT.READ`       |
| `argus.events.memory.on_tick`       | `MemoryTickData`              | `SCRIPT.READ`       |
| `argus.events.disk.on_tick`         | `list[DiskTickData]`          | `SYSTEM.READ`       |
| `argus.events.disk.on_read`         | `DiskTickData`                | `SYSTEM.READ`       |
| `argus.events.disk.on_write`        | `DiskTickData`                | `SYSTEM.READ`       |
| `argus.events.net.on_tick`          | `list[NetworkTickData]`       | `SYSTEM.READ`       |
| `argus.events.net.on_rx`            | `NetworkTickData`             | `SYSTEM.READ`       |
| `argus.events.net.on_tx`            | `NetworkTickData`             | `SYSTEM.READ`       |
| `argus.events.process.on_tick`      | `list[ProcessTickData]`       | `SYSTEM.READ`       |
| `argus.events.process.on_spawn`     | `ProcessTickData`             | `SYSTEM.READ`       |
| `argus.events.process.on_exit`      | `ProcessTickData`             | `SYSTEM.READ`       |
| `argus.events.gpu.on_tick`          | `GpuTickData \| None`         | `SYSTEM.READ`       |
| `argus.events.battery.on_tick`      | `BatteryTickData \| None`     | `SYSTEM.READ`       |
| `argus.events.sensor.on_tick`       | `list[SensorTickData] \| None`| `SYSTEM.READ`       |
| `argus.events.users.on_tick`        | `list[UserTickData] \| None`  | `SYSTEM.READ`       |

The `ctx` parameter is a Lua table with a `data` field that holds the
payload. Most payloads are Lua tables mirroring the Python TypedDict
structure. List payloads (disk, net, process, etc.) are Lua arrays.

### Engine lifecycle hooks (planned)

The following general-purpose hooks are documented in the scripting reference
but are not yet wired to the engine dispatch loop:

- `on_tick(ctx)` -- called every tick
- `on_start(ctx)` -- on engine start
- `on_stop(ctx)` -- on engine stop
- `on_config_change(ctx)` -- on config reload

Use the per-subsystem event hooks (above) for tick data in the current
release.

## Sandbox API

The `argus` table is the only bridge to engine functionality. It has three
sub-namespaces: `lifecycle`, `events`, and `api`.

### `argus.api` functions

| Function                              | Description                                  |
|---------------------------------------|----------------------------------------------|
| `argus.api.print(msg)`                | Capture a message to the script output buffer|
| `argus.api.log(msg)`                  | Alias for `print`                            |
| `argus.api.sleep(ms)`                 | Skip ticks for `ms` milliseconds (cooldown)  |
| `argus.api.timestamp()`               | Current Unix timestamp (seconds)             |
| `argus.api.format_bytes(size)`        | Format byte count (e.g. `"1.5G"`)            |
| `argus.api.format_duration(secs)`     | Format seconds (e.g. `"2m 30s"`)             |
| `argus.api.kill_process(pid)`         | Kill a process by PID (requires permission)  |

The global `print()` is aliased to `argus.api.print` so scripts can use
plain `print("text")`.

### Blocked globals

The following Lua globals are set to `None` in the sandbox and cannot be
used:

```
collectgarbage  coroutine  debug    dofile  io      load
loadfile        os         package  rawequal  rawget  rawset
require
```

Calling any of these produces a Lua runtime error.

### Permission gating

Some API functions and event subscriptions check the script's declared
permissions (from `METADATA.permissions`):

- `argus.api.kill_process(pid)` requires `PROCESSES.EXECUTE`. Without it,
  the function prints a denial message and returns `false`.
- Subsystem events under `SYSTEM.READ` (disk, net, process, gpu, battery,
  sensor, users) are only captured if the script declares `SYSTEM.READ`.

### Cooldown / sleep

`argus.api.sleep(ms)` puts the script into a cooldown state. The engine
skips all event dispatches to the script until the cooldown expires. This
is not a blocking sleep -- it returns immediately and the engine checks the
cooldown on the next dispatch.

## Script metadata

Lua scripts declare metadata in a global `METADATA` table:

```lua
METADATA = {
    name = "My Script",
    author = "You",
    version = "1.0.0",
    permissions = {"SYSTEM.READ"},
    compatible = {
        "sys.platform EQ 'win32' -> TRUE",
        "sys.platform EQ 'linux' -> TRUE",
    }
}
```

The `compatible` list uses the same compatibility rule syntax as Python
scripts and drivers.

## Example 1: Disk Watchdog

Source: `scripts/disk_watchdog.lua`

```lua
---@module 'argus'

-- Disk Watchdog -- warns when any volume exceeds capacity threshold

METADATA = {
    name = "Disk Watchdog",
    author = "Argus Team",
    version = "1.0.0",
    permissions = {"SYSTEM.READ"},
    compatible = {
        "sys.platform EQ 'win32' -> TRUE",
        "sys.platform EQ 'linux' -> TRUE",
        "sys.platform EQ 'darwin' -> TRUE",
    }
}

local threshold = 90.0
local warned = {}

function argus.lifecycle.on_load(ctx)
    print("[Disk Watchdog] Alert when any volume exceeds " .. threshold .. "%")
end

argus.events.disk.on_tick = function(ctx)
    if not ctx then return end
    local storage = ctx["data"]
    if not storage then return end
    for _, vol in ipairs(storage) do
        local pct = vol["percent"]
        local mp = vol["mount_point"]
        if pct > threshold then
            if not warned[mp] then
                warned[mp] = true
                print(string.format("[DISK] %s at %.1f%% (%s free) -- THRESHOLD EXCEEDED",
                    mp, pct, argus.api.format_bytes(vol["free_bytes"])))
            end
        else
            if warned[mp] then
                warned[mp] = nil
                print("[DISK] " .. mp .. " recovered -- now at "
                    .. string.format("%.1f", pct) .. "%")
            end
        end
    end
end
```

This script:
- Alerts when any disk volume exceeds 90% usage.
- Uses a `warned` table to avoid repeated alerts.
- Calls `argus.api.format_bytes()` to display free space in human-readable
  form.
- Tracks recovered volumes and prints a recovery message.

## Example 2: System Summary

Source: `scripts/system_summary.lua`

```lua
---@module 'argus'

-- System Summary -- compact overview of CPU, RAM, and GPU

METADATA = {
    name = "System Summary",
    author = "Argus Team",
    version = "1.0.0",
    permissions = {"SYSTEM.READ"},
    compatible = {
        "sys.platform EQ 'win32' -> TRUE",
        "sys.platform EQ 'linux' -> TRUE",
        "sys.platform EQ 'darwin' -> TRUE",
    }
}

local tick_count = 0

function argus.lifecycle.on_load(ctx)
    print("[Summary] Argus system monitor active")
end

function argus.lifecycle.on_unload(ctx)
    print("[Summary] Shutting down")
end

function argus.events.general.on_tick(ctx)
    tick_count = tick_count + 1
    local state = ctx["data"]
    local cpu = state["cpu"]
    local ram = state["ram"]
    local gpu = state["gpu"]
    local bat = state["battery"]
    local procs = state["processes"]

    local parts = {}
    parts[#parts + 1] = string.format("CPU %5.1f%%", cpu["usage_percent"])
    parts[#parts + 1] = string.format("RAM %5.1f%%", ram["percent"])

    if procs then
        parts[#parts + 1] = #procs .. " procs"
    end

    if gpu and #gpu > 0 then
        local g = gpu[1]
        parts[#parts + 1] = string.format("%s %4.0f%%", g["name"], g["usage_percent"])
    end

    if bat then
        local b = string.format("Bat %.0f%%", bat["percent"])
        if bat["power_plugged"] == true then
            b = b .. " AC"
        end
        parts[#parts + 1] = b
    end

    local line = "[Summary] " .. table.concat(parts, " | ")
    print(line)
end
```

This script:
- Subscribes to `argus.events.general.on_tick` to receive the full system
  state in one callback.
- Builds a compact single-line summary of CPU, RAM, process count, GPU, and
  battery status.
- Demonstrates both `on_load` and `on_unload` lifecycle hooks.

## Best practices

**Error handling.** Wrap callback bodies in `pcall()` to catch Lua errors.
An unhandled error disables the callback for the current tick but does not
crash the engine.

```lua
argus.events.cpu.on_tick = function(ctx)
    local ok, err = pcall(function()
        -- callback logic
    end)
    if not ok then
        print("Error: " .. tostring(err))
    end
end
```

**Sandbox limitations.** You cannot use `io`, `os`, `require`, or `dofile`.
File system access and process spawning are not available. Use the
`argus.api` functions for all side effects.

**Performance.** Keep callbacks fast. The engine runs Lua callbacks
synchronously in the tick loop by default (NONBLOCKING mode). Heavy
computation blocks the next tick.

**State persistence.** Local variables declared outside callbacks persist
across ticks. Use them to track state, implement debounce, or cache values
across dispatches.

**Permission declarations.** Always declare the minimum permissions your
script needs. Subsystem events that require `SYSTEM.READ` will not fire for
scripts that omit it. `kill_process` requires `PROCESSES.EXECUTE`.
