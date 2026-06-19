"""
CLI demo that exercises the full backend.

Usage:
    python main_console.py [--ticks N] [--interval N] [--verbose]

Reports driver inventory, loaded scripts, system metrics,
script output, and a final DB summary.
"""

from __future__ import annotations

import argparse
import time

from backend.core.engine import BackendEngine
from backend.core.loader import DriverCandidate
from backend.interfaces.enums import ConfidenceScore
from backend.storage.config import ArgusConfig
from backend.storage.database import DatabaseManager


def _confidence_label(score: ConfidenceScore) -> str:
    labels = {
        ConfidenceScore.FULL: "FULL",
        ConfidenceScore.HIGH: "HIGH",
        ConfidenceScore.MEDIUM: "MEDIUM",
        ConfidenceScore.LOW: "LOW",
        ConfidenceScore.INCOMPATIBLE: "INCOMPATIBLE",
    }
    return labels.get(score, str(score))


def _report_drivers(candidates: list[DriverCandidate]) -> None:
    print("\n  Drivers:")
    if not candidates:
        print("    (none found)")
        return
    for c in candidates:
        m = c.meta
        tag = "LOADED" if c.loaded else _confidence_label(c.score)
        print(
            f"    [{tag}] {c.file_path.name} ({m['name']} v{m['version']} by {m['author']})"
        )


def _report_scripts(scripts: list) -> None:
    print(f"\n  Scripts ({len(scripts)} loaded):")
    if not scripts:
        print("    (none)")
        return
    for i, s in enumerate(scripts, 1):
        m = s.METADATA
        perms = ", ".join(str(p) for p in m.get("permissions", []))
        print(
            f"    [{i}] {m.get('name', '?')} v{m.get('version', '?')} by {m.get('author', '?')}"
        )
        print(f"         permissions: {perms}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Argus backend demo")
    parser.add_argument(
        "--ticks", type=int, default=10, help="Number of sampling ticks (0=infinite)"
    )
    parser.add_argument(
        "--interval", type=float, default=1.0, help="Seconds between ticks"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Show storage and sensor details"
    )
    args = parser.parse_args()

    print("=== Booting Application ===\n")

    config = ArgusConfig()
    db = DatabaseManager()
    engine = BackendEngine(db=db)

    driver = engine.loader.active_driver

    print("Discovery Report:")
    print(f"  Plugin root: {engine.loader.root_dir.resolve()}")

    _report_drivers(engine.loader.all_candidates)

    if driver:
        caps = driver.get_capabilities()
        loaded = [c for c in engine.loader.all_candidates if c.loaded]
        meta = loaded[0].meta if loaded else {}
        name = meta.get("name", "?")
        version = meta.get("version", "?")
        author = meta.get("author", "?")
        perms = meta.get("permissions", [])
        print(f"\n  Active Driver: {name} v{version} by {author}")
        print(f"    Permissions: {', '.join(str(p) for p in perms)}")
        print(
            f"    Capabilities: cpu={caps.cpu.present}, gpu={caps.gpu.present}, "
            f"storage={caps.storage.present}, network={caps.network.present}, "
            f"sensors={caps.sensors.present}, battery={caps.battery.present}"
        )
    else:
        print("\n  CRITICAL: No compatible driver found.")

    _report_scripts(engine.loader.active_scripts)

    print("\n  Config:")
    print(f"    theme={config.theme}, poll_interval_ms={config.poll_interval_ms}")
    print(f"    driver_override={config.driver_override}")
    print(f"    database_retention_days={config.database_retention_days}")

    print(
        f"\n=== Event Loop Started ({args.ticks} ticks, {args.interval}s interval) ===\n"
    )

    tick_count = 0
    try:
        while args.ticks == 0 or tick_count < args.ticks:
            start = time.monotonic()
            state = engine.get_system_state()

            if "error" in state:
                print(f"ERROR: {state['error']}")
                break

            tick_count += 1
            cpu = state["cpu"]
            ram = state["ram"]

            # --- Core metrics ---
            print(
                f"[{tick_count:>3}] CPU: {cpu['usage_percent']:5.1f}% "
                f"({cpu['physical_cores']}C/{cpu['logical_cores']}T)  "
                f"| RAM: {ram['percent']:5.1f}% "
                f"({ram['used_bytes'] >> 20}MB / {ram['total_bytes'] >> 20}MB)"
            )

            # --- Top process ---
            procs = state.get("processes")
            if procs:
                top = sorted(procs, key=lambda p: p["cpu_percent"], reverse=True)[0]
                print(
                    f"         Top: PID {top['pid']:<6} {top['name']:<20s} @ {top['cpu_percent']:5.1f}%"
                )

            # --- Network ---
            net = state.get("network")
            if net:
                n = net[0]
                print(
                    f"         Net: {n['bytes_sent'] >> 10:>8}KB sent "
                    f"/ {n['bytes_recv'] >> 10:>8}KB recv"
                )

            # --- GPU ---
            gpu = state.get("gpu")
            if gpu:
                for g in gpu:
                    print(
                        f"         GPU: {g['name']} @ {g['usage_percent']:4.0f}% "
                        f"({g['memory_used'] >> 20}MB / {g['memory_total'] >> 20}MB)"
                    )

            # --- Battery ---
            battery = state.get("battery")
            if battery:
                plugged = "plugged" if battery.get("power_plugged") else "on battery"
                print(f"         Battery: {battery['percent']:5.1f}% ({plugged})")

            # --- Storage (verbose) ---
            storage = state.get("storage")
            if args.verbose and storage:
                for vol in storage:
                    print(
                        f"         Disk {vol['mount_point']}: "
                        f"{vol['percent']:5.1f}% "
                        f"({vol['used_bytes'] >> 20}MB / {vol['total_bytes'] >> 20}MB)"
                    )

            # --- Sensors (verbose) ---
            sensors = state.get("sensors")
            if args.verbose and sensors:
                for s in sensors:
                    print(
                        f"         Sensor {s['name']}: {s['value']:.1f} {s.get('unit', '?')}"
                    )

            # --- Script output ---
            for script in engine.loader.active_scripts:
                if hasattr(script, "pop_output"):
                    for line in script.pop_output():
                        name = script.METADATA.get("name", "?")
                        print(f"  [{name}] {line}")

            elapsed = time.monotonic() - start
            sleep_time = max(0.0, args.interval - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("\n  Interrupted by user")

    rows = db.query_range("2000-01-01", "2100-01-01")
    print(f"\n  DB entries: {len(rows)} (across {tick_count} ticks)")
    db.close()


if __name__ == "__main__":
    main()
