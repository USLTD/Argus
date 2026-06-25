---@module 'argus'

-- Process Watchdog — detects runaway processes by CPU threshold
-- Logs escalating alerts on sustained high CPU; no auto-kill.

METADATA = {
    name = "Process Watchdog",
    author = "Argus Team",
    version = "2.0.0",
    permissions = {"SYSTEM.READ"},
    compatible = {
        "sys.platform EQ 'win32' -> TRUE",
        "sys.platform EQ 'linux' -> TRUE",
        "sys.platform EQ 'darwin' -> TRUE",
    }
}

local cpu_threshold = 95.0
local sustained_alert_threshold = 3
local known_bad = {}

function argus.lifecycle.on_load(ctx)
    print(string.format("[ProcWatch] Monitoring processes > %.0f%% CPU", cpu_threshold))
end

argus.events.process.on_tick = function(ctx)
    if not ctx then return end
    local processes = ctx["data"]
    if not processes then return end
    for _, p in ipairs(processes) do
        local pid = p["pid"]
        local name = p["name"]
        local cpu = p["cpu_percent"]
        if cpu > cpu_threshold then
            if not known_bad[pid] then
                known_bad[pid] = {count = 1, name = name}
                print(string.format("[ProcWatch] %s (PID %d) at %.1f%% CPU — ALERT", name, pid, cpu))
            else
                known_bad[pid].count = known_bad[pid].count + 1
                if known_bad[pid].count >= sustained_alert_threshold then
                    print(string.format("[ProcWatch] %s (PID %d) sustained >%.0f%% CPU for %d ticks", name, pid, cpu_threshold, known_bad[pid].count))
                end
            end
        else
            known_bad[pid] = nil
        end
    end
end
