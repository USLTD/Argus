"""
CLI demo that exercises the full backend.

Usage:
    python main_console.py [--ticks N] [--interval N] [--verbose] [--debug]

Reports driver inventory, loaded scripts, system metrics,
script output, and a final DB summary.
"""

from __future__ import annotations

import argparse
import time

import psutil
from rich.console import Console
from rich.table import Table

from backend.core.engine import BackendEngine
from backend.core.loader import DriverCandidate
from backend.interfaces.enums import ConfidenceScore
from backend.storage.config import ArgusConfig
from frontend.core.database import DatabaseManager
from frontend.core.metrics_converter import snapshot_to_system_metrics


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
        "--interval", type=float, default=None, help="Seconds between ticks (default: from config.poll_interval_ms)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show storage (all mount points) and sensor details",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Show ALL subsystems (users, top processes, all sensors, all mount points)",
    )
    args = parser.parse_args()

    console = Console()
    is_verbose = args.verbose or args.debug

    print("=== Booting Application ===\n")

    config = ArgusConfig()
    interval = args.interval if args.interval is not None else config.poll_interval_ms / 1000
    db = DatabaseManager()
    engine = BackendEngine(
        on_tick_callback=lambda snap: db.write_snapshot(
            snapshot_to_system_metrics(snap)
        )
    )

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
            f"    Capabilities: cpu={caps.cpu.present}, gpu={caps.gpu.present}, "  # type: ignore[union-attr]
            f"storage={caps.storage.present}, network={caps.network.present}, "  # type: ignore[union-attr]
            f"sensors={caps.sensors.present}, battery={caps.battery.present}"  # type: ignore[union-attr]
        )
    else:
        print("\n  CRITICAL: No compatible driver found.")

    _report_scripts(engine.loader.active_scripts)

    print("\n  Config:")
    print(f"    poll_interval_ms={config.poll_interval_ms}ms (using --interval={interval}s)")
    print(f"    driver_override={config.driver_override}")

    print(
        f"\n=== Event Loop Started ({args.ticks} ticks, {interval}s interval) ===\n"
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
            cpu_data = state.get("cpu")
            if cpu_data and cpu_data.get("metrics"):
                cpu_agg = cpu_data["metrics"][0]  # core_id=None = aggregate
                cpu_usage = cpu_agg.get("usage_percent", 0.0)
                cpu_freq = cpu_agg.get("frequency_mhz")
            else:
                cpu_usage, cpu_freq = 0.0, None

            ram_data = state.get("ram")
            if ram_data and ram_data.get("metrics"):
                ram = ram_data["metrics"][0]
                ram_pct = ram.get("percent", 0.0)
                ram_used = ram.get("used_bytes", 0)
                ram_total = ram.get("total_bytes", 0)
            else:
                ram_pct, ram_used, ram_total = 0.0, 0, 0

            # --- Combined system table ---
            p_cores = psutil.cpu_count(logical=False) or 0
            l_cores = psutil.cpu_count(logical=True) or 0
            t = Table(show_header=True, header_style="bold magenta")
            t.add_column("Metric", style="cyan")
            t.add_column("Value")
            t.add_row(
                "CPU",
                f"{cpu_usage:5.1f}% ({p_cores}C/{l_cores}T)"
                + (f" @ {cpu_freq:.0f} MHz" if cpu_freq else ""),
            )
            t.add_row(
                "RAM",
                f"{ram_pct:5.1f}% ({ram_used >> 20} MB / {ram_total >> 20} MB)",
            )

            # --- Disk (first mount point always, all mounts in verbose/debug) ---
            storage_data = state.get("storage")
            if storage_data and storage_data.get("metrics"):
                first_vol = storage_data["metrics"][0]
                t.add_row(
                    "Disk",
                    f"{first_vol.get('mount_point', '?')}: {first_vol.get('percent', 0):5.1f}% "
                    f"({first_vol.get('used_bytes', 0) >> 20} MB / {first_vol.get('total_bytes', 0) >> 20} MB)",
                )

            # --- Network ---
            net_data = state.get("network")
            if net_data and net_data.get("metrics"):
                nets = net_data["metrics"]
                n = nets[0]
                t.add_row("Net Sent", f"{n.get('bytes_sent', 0) >> 10:>8} KB")
                t.add_row("Net Recv", f"{n.get('bytes_recv', 0) >> 10:>8} KB")

            # --- GPU ---
            gpu_data = state.get("gpu")
            if gpu_data and gpu_data.get("metrics"):
                for g in gpu_data["metrics"]:
                    t.add_row(
                        f"GPU {g.get('name', '?')}",
                        f"{g.get('usage_percent', 0):4.0f}% "
                        f"({g.get('memory_used', 0) >> 20} MB / {g.get('memory_total', 0) >> 20} MB)",
                    )

            # --- Battery ---
            battery_data = state.get("battery")
            if battery_data and battery_data.get("metrics"):
                bat = battery_data["metrics"][0]
                plugged = "plugged" if bat.get("power_plugged") else "on battery"
                t.add_row("Battery", f"{bat.get('percent', 0):5.1f}% ({plugged})")

            # --- Top process ---
            procs_data = state.get("processes")
            if procs_data and procs_data.get("metrics"):
                procs = procs_data["metrics"]
                top = sorted(
                    procs, key=lambda p: p.get("cpu_percent", 0), reverse=True
                )[0]
                t.add_row(
                    "Top Proc",
                    f"PID {top['pid']} {top.get('name', '?')} @ {top.get('cpu_percent', 0):5.1f}%",
                )

            console.print()
            console.print(t)

            # --- Storage: verbose / debug ---
            if is_verbose and storage_data and storage_data.get("metrics"):
                st = Table(
                    show_header=True,
                    header_style="bold magenta",
                    title="Storage",
                )
                st.add_column("Mount", style="cyan")
                st.add_column("Usage", justify="right")
                st.add_column("Used", justify="right")
                st.add_column("Total", justify="right")
                for vol in storage_data["metrics"]:
                    st.add_row(
                        vol.get("mount_point", "?"),
                        f"{vol.get('percent', 0):5.1f}%",
                        f"{vol.get('used_bytes', 0) >> 20} MB",
                        f"{vol.get('total_bytes', 0) >> 20} MB",
                    )
                console.print(st)

            # --- Sensors: verbose / debug ---
            sensors_data = state.get("sensors")
            if is_verbose and sensors_data and sensors_data.get("metrics"):
                st = Table(
                    show_header=True,
                    header_style="bold magenta",
                    title="Sensors",
                )
                st.add_column("Name", style="cyan")
                st.add_column("Value", justify="right")
                st.add_column("Unit")
                for s in sensors_data["metrics"]:
                    st.add_row(
                        s.get("name", "?"),
                        f"{s.get('value', 0):.1f}",
                        s.get("unit", "?"),
                    )
                console.print(st)

            # --- Debug-only sections ---
            if args.debug:
                # --- Users ---
                users_data = state.get("users")
                if users_data and users_data.get("metrics"):
                    ut = Table(
                        show_header=True,
                        header_style="bold magenta",
                        title="Users",
                    )
                    ut.add_column("User", style="cyan")
                    ut.add_column("Terminal")
                    ut.add_column("Host")
                    ut.add_column("Started")
                    for u in users_data["metrics"]:
                        ut.add_row(
                            u.get("name", "?"),
                            str(u.get("terminal", "?")),
                            str(u.get("host", "?")),
                            str(u.get("started", "?")),
                        )
                    console.print(ut)

                # --- Top 5 processes by CPU ---
                if procs_data and procs_data.get("metrics"):
                    sorted_procs = sorted(
                        procs_data["metrics"],
                        key=lambda p: p.get("cpu_percent", 0),
                        reverse=True,
                    )[:5]
                    pt = Table(
                        show_header=True,
                        header_style="bold magenta",
                        title="Top Processes (by CPU)",
                    )
                    pt.add_column("PID", justify="right", style="cyan")
                    pt.add_column("Name")
                    pt.add_column("CPU%", justify="right")
                    pt.add_column("Memory%", justify="right")
                    for p in sorted_procs:
                        pt.add_row(
                            str(p.get("pid", "?")),
                            str(p.get("name", "?")),
                            f"{p.get('cpu_percent', 0):5.1f}",
                            f"{p.get('memory_percent', 0):5.1f}",
                        )
                    console.print(pt)

            # --- Script output ---
            for script in engine.loader.active_scripts:
                if hasattr(script, "pop_output"):
                    for line in script.pop_output():
                        name = script.METADATA.get("name", "?")  # type: ignore[union-attr]
                        print(f"  [{name}] {line}")

            elapsed = time.monotonic() - start
            sleep_time = max(0.0, interval - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("\n  Interrupted by user")

    rows = db.query_range("2000-01-01", "2100-01-01")
    print(f"\n  DB entries: {len(rows)} (across {tick_count} ticks)")
    db.close()


if __name__ == "__main__":
    main()
