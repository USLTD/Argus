from enum import IntEnum, StrEnum


class ConfidenceScore(IntEnum):
    INCOMPATIBLE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    FULL = 4


class CompatAction(StrEnum):
    LOAD = "load"
    SKIP = "skip"


class Permission(StrEnum):
    SCRIPT_READ_ONLY = "SCRIPT.READ_ONLY"
    SYSTEM_READ = "SYSTEM.READ"
    PROCESS_KILL = "PROCESS.KILL"
