"""Sentinel types for per-subsystem tick methods.

``Unavailable`` is returned by a driver tick method when the data
cannot be produced — distinguishing "not supported" from "fetch
failed" from actual data.

``TickSnapshot`` is the typed aggregate returned by
:meth:`BaseDriver.tick` / :meth:`BackendEngine.tick`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.interfaces.caps import (
        BatteryMetric,
        CPUMetric,
        GPUMetric,
        MemoryMetric,
        MetricsCollection,
        NetworkMetric,
        ProcessMetric,
        SensorMetric,
        StorageMetric,
    )


@dataclass(frozen=True)
class Unavailable:
    """Returned by tick methods when data cannot be produced.

    ``reason`` is a short machine-readable code:

    * ``"unsupported"`` — capability absent (e.g. no GPU on this system)
    * ``"error"`` — the fetch call raised an exception
    * ``"timeout"`` — the fetch timed out
    * ``"disabled"`` — explicitly disabled by configuration

    ``detail`` is an optional human-readable explanation.
    """

    reason: str
    detail: str = ""


@dataclass
class TickSnapshot:
    """Typed aggregate returned by :meth:`BaseDriver.tick`.

    Each field is either the concrete metric or :class:`Unavailable`.
    """

    cpu: MetricsCollection[CPUMetric] | Unavailable
    memory: MetricsCollection[MemoryMetric] | Unavailable
    processes: MetricsCollection[ProcessMetric] | Unavailable
    disk: MetricsCollection[StorageMetric] | Unavailable
    network: MetricsCollection[NetworkMetric] | Unavailable
    gpu: MetricsCollection[GPUMetric] | Unavailable
    sensors: MetricsCollection[SensorMetric] | Unavailable
    battery: MetricsCollection[BatteryMetric] | Unavailable
