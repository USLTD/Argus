"""CPU Logger — prints CPU usage and core count on each tick."""

from __future__ import annotations

import argus

METADATA: argus.script.Metadata = {
    "name": "CPU Logger",
    "author": "Argus Team",
    "version": "2.0.0",
    "compatible": [
        "sys.platform EQ 'win32' -> TRUE",
        "sys.platform EQ 'linux' -> TRUE",
        "sys.platform EQ 'darwin' -> TRUE",
    ],
}


@argus.lifecycle.on_load
def on_load(ctx) -> None:
    argus.api.print("Loading CPU Logger...")


@argus.lifecycle.on_unload
def on_unload(ctx) -> None:
    argus.api.print("Unloading CPU Logger...")


@argus.events.cpu.on_tick  # type: ignore[arg-type]
def on_cpu(ctx: object) -> None:
    data = ctx.data  # type: ignore[union-attr]
    cores = data.get("physical_cores", "?")
    threads = data.get("logical_cores", "?")
    print(f"[CPU] {data['usage_percent']:.1f}% ({cores}C/{threads}T)")
