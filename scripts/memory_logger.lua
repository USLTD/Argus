-- Memory Logger — reports significant RAM usage changes

METADATA = {
    name = "Memory Logger",
    author = "Core Team",
    version = "1.0.0",
    permissions = {"SCRIPT.READ_ONLY"},
    compatible = {
        "sys.platform EQ 'win32' -> TRUE",
        "sys.platform EQ 'linux' -> TRUE",
        "sys.platform EQ 'darwin' -> TRUE",
    }
}

local last_percent = 0

argus.events.on_tick = function(state)
    local ram = state["ram"]
    if not ram then return end

    local current = ram["percent"]
    local delta = current - last_percent

    if last_percent > 0 and math.abs(delta) >= 5.0 then
        if delta > 0 then
            print("RAM increased by " .. string.format("%.1f", delta) .. "% — now at " .. string.format("%.1f", current) .. "%")
        else
            print("RAM decreased by " .. string.format("%.1f", math.abs(delta)) .. "% — now at " .. string.format("%.1f", current) .. "%")
        end
    end

    last_percent = current
end
