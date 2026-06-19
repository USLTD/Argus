---@module 'argus'

-- System Summary — compact overview of CPU, RAM, and GPU
-- Demonstrates hooks + multi-event subscription.
-- Uses on_load for startup message, then multiple on_tick handlers.

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

function argus.events.general.on_tick(state)
    tick_count = tick_count + 1
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
