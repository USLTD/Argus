---@meta

---@class CpuMetrics
---@field usage_percent number
---@field physical_cores integer
---@field logical_cores integer
---@field per_cpu number[]|nil
---@field frequency number|nil

---@class RamMetrics
---@field percent number
---@field total_bytes number
---@field used_bytes number
---@field available_bytes number

---@class DiskVolumeInfo
---@field mount_point string
---@field fstype string
---@field total_bytes number
---@field used_bytes number
---@field free_bytes number
---@field percent number

---@class ProcessInfo
---@field pid integer
---@field name string
---@field cpu_percent number
---@field memory_rss number|nil
---@field status string|nil
---@field username string|nil

---@class NetMetrics
---@field bytes_sent number
---@field bytes_recv number
---@field packets_sent number|nil
---@field packets_recv number|nil

---@class GpuInfo
---@field name string
---@field usage_percent number
---@field memory_total number|nil
---@field memory_used number|nil

---@class BatteryMetrics
---@field percent number
---@field power_plugged boolean|nil
---@field seconds_left number|nil

---@class SensorInfo
---@field name string
---@field value number
---@field unit string

---@class argus_lifecycle
---@field on_load (fun(ctx: table)|nil) Called after the script is loaded and activated
---@field on_unload (fun(ctx: table)|nil) Called before the script is unloaded

---@class argus_events_general
---@field on_tick (fun(state: table)|nil) Called with the full system state

---@class argus_events_cpu
---@field on_tick (fun(cpu: CpuMetrics)|nil) Called with CPU metrics only

---@class argus_events_memory
---@field on_tick (fun(mem: RamMetrics)|nil) Called with memory metrics only

---@class argus_events_disk
---@field on_tick (fun(disk: DiskVolumeInfo[])|nil) Called with disk metrics (requires SYSTEM.READ)

---@class argus_events_net
---@field on_tick (fun(net: NetMetrics[])|nil) Called with network metrics (requires SYSTEM.READ)

---@class argus_events_process
---@field on_tick (fun(proc: ProcessInfo[])|nil) Called with process list (requires SYSTEM.READ)

---@class argus_events_gpu
---@field on_tick (fun(gpu: GpuInfo[]|nil)|nil) Called with GPU metrics (requires SYSTEM.READ)

---@class argus_events_battery
---@field on_tick (fun(bat: BatteryMetrics|nil)|nil) Called with battery metrics (requires SYSTEM.READ)

---@class argus_events_sensor
---@field on_tick (fun(sensors: SensorInfo[]|nil)|nil) Called with sensor metrics (requires SYSTEM.READ)

---@class argus_events
---@field general argus_events_general
---@field cpu argus_events_cpu
---@field memory argus_events_memory
---@field disk argus_events_disk
---@field net argus_events_net
---@field process argus_events_process
---@field gpu argus_events_gpu
---@field battery argus_events_battery
---@field sensor argus_events_sensor

---@class argus_api
---@field print fun(...): nil
---@field log fun(...): nil
---@field sleep fun(ms: number): nil
---@field timestamp fun(): number
---@field format_bytes fun(size: number): string
---@field format_duration fun(sec: number): string
---@field kill_process fun(pid: number): boolean

---@class argus
---@field lifecycle argus_lifecycle
---@field events argus_events
---@field api argus_api

--- Argus Lua Script API Reference.
---
--- Every script **must** declare a module-level METADATA table:
---
--- ```lua
--- METADATA = {
---   name = "my-script",
---   author = "You",
---   version = "1.0.0",
---   permissions = { "SCRIPT.READ_ONLY" },
---   compatible = { "TRUE -> TRUE" }
--- }
--- ```
---
--- Available permissions:
---   SCRIPT.READ_ONLY — lifecycle + general/cpu/memory events
---   SYSTEM.READ     — adds disk/net/process/gpu/battery/sensor events
---   PROCESS.KILL    — enables argus.api.kill_process()
---
--- @module argus
argus = {}
argus.lifecycle = {}
argus.events = {}
argus.events.general = {}
argus.events.cpu = {}
argus.events.memory = {}
argus.events.disk = {}
argus.events.net = {}
argus.events.process = {}
argus.events.gpu = {}
argus.events.battery = {}
argus.events.sensor = {}
argus.api = {}
