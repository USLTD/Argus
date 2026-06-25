---@module 'argus'

-- Sensor Dashboard — pretty-prints temperature sensors
-- Subscribes to sensor.on_tick (requires SYSTEM.READ).
-- Reports every 6 ticks to reduce noise.

METADATA = {
    name = "Sensor Dashboard",
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

argus.events.sensor.on_tick = function(ctx)
    if not ctx then return end
    local sensors = ctx["data"]
    if not sensors or #sensors == 0 then return end
    tick_count = tick_count + 1
    if tick_count < 6 then return end
    tick_count = 0

    print("--- Sensors ---")
    for _, s in ipairs(sensors) do
        print(string.format("  %-30s %6.1f °C", s["name"], s["value"]))
    end
end
