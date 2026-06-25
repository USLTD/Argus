"""Subsystem event injectors.

Permission gating:
* ``SCRIPT.READ`` — general, cpu, memory
* ``SYSTEM.READ`` — disk, net, process, gpu, battery, sensor
"""

from backend.interfaces.enums import Permission
from backend.core.injectors import EventInjector

_RO = Permission.SCRIPT_READ
_SR = Permission.SYSTEM_READ


def get_events_injectors() -> list[EventInjector]:
    return [
        EventInjector("events.general", ["on_tick"], permission=_RO),
        EventInjector("events.cpu", ["on_tick"], permission=_RO),
        EventInjector("events.memory", ["on_tick"], permission=_RO),
        EventInjector(
            "events.disk", ["on_tick", "on_read", "on_write"], permission=_SR
        ),
        EventInjector("events.net", ["on_tick", "on_rx", "on_tx"], permission=_SR),
        EventInjector(
            "events.process", ["on_tick", "on_spawn", "on_exit"], permission=_SR
        ),
        EventInjector("events.gpu", ["on_tick"], permission=_SR),
        EventInjector("events.battery", ["on_tick"], permission=_SR),
        EventInjector("events.sensor", ["on_tick"], permission=_SR),
    ]
