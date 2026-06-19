---@module 'argus'

-- Disk Watchdog — warns when any volume exceeds capacity threshold
-- Subscribes to disk.on_tick (requires SYSTEM.READ).

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

argus.events.disk.on_tick = function(storage)
    if not storage then return end
    for _, vol in ipairs(storage) do
        local pct = vol["percent"]
        local mp = vol["mount_point"]
        if pct > threshold then
            if not warned[mp] then
                warned[mp] = true
                print(string.format("[DISK] %s at %.1f%% (%s free) — THRESHOLD EXCEEDED", mp, pct, argus.api.format_bytes(vol["free_bytes"])))
            end
        else
            if warned[mp] then
                warned[mp] = nil
                print("[DISK] " .. mp .. " recovered — now at " .. string.format("%.1f", pct) .. "%")
            end
        end
    end
end
