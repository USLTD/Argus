---@meta

--- ── Metric types (Python model names) ─────────────────────────

--- CPU metrics (aggregate).
---@class CPUMetric
---@field usage_percent number
---@field physical_cores integer
---@field logical_cores integer
---@field per_core number[]
---@field frequency number|nil

--- Memory (RAM) metrics.
---@class MemoryMetric
---@field percent number
---@field total_bytes integer
---@field used_bytes integer
---@field available_bytes integer

--- A single disk/storage volume.
---@class StorageMetric
---@field mount_point string
---@field fstype string
---@field total_bytes integer
---@field used_bytes integer
---@field free_bytes integer
---@field percent number

--- A single process.
---@class ProcessMetric
---@field pid integer
---@field name string
---@field cpu_percent number
---@field memory_rss integer|nil
---@field status string|nil
---@field username string|nil

--- A single network interface.
---@class NetworkMetric
---@field bytes_sent integer
---@field bytes_recv integer
---@field packets_sent integer|nil
---@field packets_recv integer|nil

--- A single GPU.
---@class GPUMetric
---@field name string
---@field usage_percent number
---@field memory_total integer|nil
---@field memory_used integer|nil

--- Battery status.
---@class BatteryMetric
---@field percent number
---@field power_plugged boolean|nil
---@field seconds_left number|nil

--- A single sensor reading.
---@class SensorMetric
---@field name string
---@field value number
---@field unit string
---@field category string

--- A single logged-in user.
---@class UserMetric
---@field name string
---@field terminal string|nil
---@field host string|nil
---@field started number

--- ── Script context ─────────────────────────────────────────────

--- Context wrapper passed to all event and lifecycle callbacks.
--- Access the per-hook payload via `ctx["data"]`.
---@class ScriptContext
---@field data table
---@field config table|nil
---@field db table|nil
---@field driver table|nil

--- ── TickData TypedDict-style types ────────────────────────────

--- Full system state snapshot delivered by `general.on_tick`.
---@class GeneralTickData
---@field cpu CpuTickData
---@field ram MemoryTickData
---@field processes ProcessTickData[]|nil
---@field storage DiskTickData[]
---@field gpu GpuTickData[]|nil
---@field network NetworkTickData[]|nil
---@field sensors SensorTickData[]|nil
---@field battery BatteryTickData|nil
---@field users UserTickData[]|nil
---@field extra table

--- CPU metrics for a single tick.
---@class CpuTickData
---@field usage_percent number
---@field per_core number[]
---@field physical_cores integer
---@field logical_cores integer
---@field frequency number|nil

--- Memory (RAM) metrics for a single tick.
---@class MemoryTickData
---@field total_bytes integer
---@field used_bytes integer
---@field available_bytes integer
---@field percent number

--- A single disk volume snapshot.
---@class DiskTickData
---@field mount_point string
---@field total_bytes integer
---@field used_bytes integer
---@field free_bytes integer
---@field percent number

--- A single network interface snapshot.
---@class NetworkTickData
---@field bytes_sent integer
---@field bytes_recv integer
---@field packets_sent integer
---@field packets_recv integer

--- A single process snapshot.
---@class ProcessTickData
---@field pid integer
---@field name string
---@field cpu_percent number
---@field memory_rss integer
---@field status string
---@field username string|nil

--- A single GPU snapshot.
---@class GpuTickData
---@field name string
---@field usage_percent number
---@field memory_total integer
---@field memory_used integer

--- Battery status snapshot.
---@class BatteryTickData
---@field percent number
---@field power_plugged boolean|nil
---@field seconds_left number|nil

--- A single sensor reading.
---@class SensorTickData
---@field name string
---@field value number
---@field unit string
---@field category string

--- A single logged-in user snapshot.
---@class UserTickData
---@field name string
---@field terminal string|nil
---@field host string|nil
---@field started number

--- ── Event namespace classes ────────────────────────────────────

--- General system events (full state).
---@class GeneralEvents
---@field on_tick fun(ctx: ScriptContext)

--- CPU subsystem events.
---@class CpuEvents
---@field on_tick fun(ctx: ScriptContext)

--- Memory subsystem events.
---@class MemoryEvents
---@field on_tick fun(ctx: ScriptContext)

--- Disk subsystem events.
---@class DiskEvents
---@field on_tick fun(ctx: ScriptContext)
---@field on_read fun(ctx: ScriptContext)
---@field on_write fun(ctx: ScriptContext)

--- Network subsystem events.
---@class NetEvents
---@field on_tick fun(ctx: ScriptContext)
---@field on_rx fun(ctx: ScriptContext)
---@field on_tx fun(ctx: ScriptContext)

--- Process subsystem events.
---@class ProcessEvents
---@field on_tick fun(ctx: ScriptContext)
---@field on_spawn fun(ctx: ScriptContext)
---@field on_exit fun(ctx: ScriptContext)

--- GPU subsystem events.
---@class GpuEvents
---@field on_tick fun(ctx: ScriptContext)

--- Battery subsystem events.
---@class BatteryEvents
---@field on_tick fun(ctx: ScriptContext)

--- Sensor subsystem events.
---@class SensorEvents
---@field on_tick fun(ctx: ScriptContext)

--- Users subsystem events.
---@class UserEvents
---@field on_tick fun(ctx: ScriptContext)

--- ── Top-level namespaces ───────────────────────────────────────

--- Collection of all subsystem event namespaces.
---@class EventsNamespace
---@field general GeneralEvents
---@field cpu CpuEvents
---@field memory MemoryEvents
---@field disk DiskEvents
---@field net NetEvents
---@field process ProcessEvents
---@field gpu GpuEvents
---@field battery BatteryEvents
---@field sensor SensorEvents
---@field users UserEvents

--- Script lifecycle hooks (on_load / on_unload).
---@class LifecycleNamespace
---@field on_load fun(ctx: ScriptContext)
---@field on_unload fun(ctx: ScriptContext)

--- Utility functions exposed by the Argus sandbox.
---@class ApiNamespace
---@field print fun(...: any)
---@field log fun(...: any)
---@field sleep fun(ms: integer)
---@field timestamp fun(): number
---@field format_bytes fun(size: number): string
---@field format_duration fun(seconds: number): string
---@field kill_process fun(pid: integer): boolean

--- ── Root argus module ──────────────────────────────────────────

---@class ArgusModule
---@field api ApiNamespace
---@field lifecycle LifecycleNamespace
---@field events EventsNamespace

---@module argus
