-- Top Process Reporter — prints top 3 CPU consumers every 5 ticks

METADATA = {
    name = "Top Process Reporter",
    author = "Core Team",
    version = "1.0.0",
    permissions = {"SCRIPT.READ_ONLY"},
    compatible = {
        "sys.platform EQ 'win32' -> TRUE",
        "sys.platform EQ 'linux' -> TRUE",
        "sys.platform EQ 'darwin' -> TRUE",
    }
}

local tick_count = 0

argus.events.on_tick = function(state)
    tick_count = tick_count + 1
    if tick_count < 5 then return end
    tick_count = 0

    local processes = state["processes"]
    if not processes then
        print("No process data available")
        return
    end

    local top = {}
    local idx = 0
    while true do
        local ok, p = pcall(function() return processes[idx] end)
        if not ok or p == nil then break end
        local cpu = p["cpu_percent"]
        if cpu then
            top[#top + 1] = {pid = p["pid"], name = p["name"], cpu = cpu}
        end
        idx = idx + 1
    end

    if #top == 0 then
        print("No process data available")
        return
    end

    for i = 1, #top do
        for j = i + 1, #top do
            if top[i]["cpu"] < top[j]["cpu"] then
                top[i], top[j] = top[j], top[i]
            end
        end
    end

    print("--- Top 3 Processes ---")
    local limit = math.min(3, #top)
    for i = 1, limit do
        local p = top[i]
        print("  " .. i .. ". PID " .. p["pid"] .. " " .. p["name"] .. " @ " .. string.format("%.1f", p["cpu"]) .. "% CPU")
    end
end
