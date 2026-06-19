"""Multi-Subsystem Reporter — prints CPU, RAM, top process, and GPU."""

from __future__ import annotations

import argus

METADATA: argus.script.Metadata = {
    "name": "Multi-Subsystem Reporter",
    "author": "Argus Team",
    "version": "2.0.0",
    "permissions": [argus.script.Permission.SYSTEM_READ],
    "compatible": [
        "sys.platform EQ 'win32' -> TRUE",
        "sys.platform EQ 'linux' -> TRUE",
        "sys.platform EQ 'darwin' -> TRUE",
    ],
}


cpu_data = {}
ram_data = {}


@argus.events.cpu.on_tick
def on_cpu(data):
    cpu_data["percent"] = data["usage_percent"]


@argus.events.memory.on_tick
def on_memory(data):
    ram_data["percent"] = data["percent"]


@argus.events.general.on_tick
def on_tick(state):
    parts = []
    parts.append(f"CPU {state['cpu']['usage_percent']:.1f}%")
    parts.append(f"RAM {state['ram']['percent']:.1f}%")

    procs = state.get("processes")
    if procs:
        top = max(procs, key=lambda p: p["cpu_percent"])
        parts.append(f"Top: {top['name']} @ {top['cpu_percent']:.1f}%")

    gpu = state.get("gpu")
    if gpu:
        g = gpu[0]
        parts.append(f"{g['name']} @ {g['usage_percent']:.0f}%")

    print(" | ".join(parts))
