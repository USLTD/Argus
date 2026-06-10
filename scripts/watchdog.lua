-- Lua Watchdog — alerts when CPU exceeds 85%

METADATA = {
    name = "High CPU Watchdog",
    author = "Power User",
    version = "1.0.0",
    permissions = {"SCRIPT.READ_ONLY"},
    compatible = {
        "sys.platform EQ 'win32' -> TRUE",
        "sys.platform EQ 'linux' -> TRUE",
        "sys.platform EQ 'darwin' -> TRUE",
    }
}

argus.events.on_tick = function(state)
    local cpu = state["cpu"]
    if cpu and cpu["usage_percent"] > 85.0 then
        print("ALERT: CPU usage " .. cpu["usage_percent"] .. "% exceeds 85% threshold")
    end
end
