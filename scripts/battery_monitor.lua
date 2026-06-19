---@module 'argus'

-- Battery Monitor — reports battery status on each tick
-- Subscribes to battery.on_tick (requires SYSTEM.READ).

METADATA = {
    name = "Battery Monitor",
    author = "Argus Team",
    version = "1.0.0",
    permissions = {"SYSTEM.READ"},
    compatible = {
        "sys.platform EQ 'win32' -> TRUE",
        "sys.platform EQ 'linux' -> TRUE",
        "sys.platform EQ 'darwin' -> TRUE",
    }
}

local last_percent = 0
local last_plugged = nil

argus.events.battery.on_tick = function(bat)
    if not bat then return end

    local pct = bat["percent"]
    local plugged = bat["power_plugged"]

    if last_plugged ~= nil and plugged ~= last_plugged then
        if plugged then
            print("[BATTERY] Plugged in at " .. string.format("%.1f", pct) .. "%")
        else
            print("[BATTERY] Unplugged at " .. string.format("%.1f", pct) .. "%")
        end
    end

    local delta = pct - last_percent
    if last_percent > 0 and math.abs(delta) >= 5.0 then
        local dir = "+"
        if delta < 0 then dir = "" end
        print(string.format("[BATTERY] %s%.1f%% — now at %.1f%%", dir, delta, pct))
    end

    if plugged == false then
        local secs = bat["seconds_left"]
        if secs then
            print("[BATTERY] " .. string.format("%.1f", pct) .. "% — " .. argus.api.format_duration(secs) .. " remaining")
        end
    end

    last_percent = pct
    last_plugged = plugged
end
