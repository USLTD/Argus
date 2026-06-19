---@module 'argus'

-- Network Activity Monitor — reports bandwidth delta per tick
-- Subscribes to net.on_tick (requires SYSTEM.READ).
-- Tracks bytes sent/recv and displays rates per second.

METADATA = {
    name = "Network Activity",
    author = "Argus Team",
    version = "1.0.0",
    permissions = {"SYSTEM.READ"},
    compatible = {
        "sys.platform EQ 'win32' -> TRUE",
        "sys.platform EQ 'linux' -> TRUE",
        "sys.platform EQ 'darwin' -> TRUE",
    }
}

local last_sent = 0
local last_recv = 0
local tick_interval = 1.0

argus.events.net.on_tick = function(net)
    if not net or #net == 0 then return end

    local iface = net[1]
    local sent = iface["bytes_sent"]
    local recv = iface["bytes_recv"]

    if last_sent > 0 then
        local sent_rate = (sent - last_sent) / tick_interval
        local recv_rate = (recv - last_recv) / tick_interval
        print(string.format("[NET] UP %s/s  DOWN %s/s", argus.api.format_bytes(sent_rate), argus.api.format_bytes(recv_rate)))
    end

    last_sent = sent
    last_recv = recv
end
