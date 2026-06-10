"""
CLI demo that exercises the full backend and reports:
- Driver inventory (all discovered, loaded, incompatible)
- Loaded driver capabilities and metadata
- Loaded scripts and their metadata
- Per-tick system metrics and script output
"""

import time

from backend.core.engine import BackendEngine
from backend.core.loader import DriverCandidate
from backend.interfaces.enums import ConfidenceScore
from backend.storage.database import DatabaseManager
from backend.storage.config import ArgusConfig


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
            f"    Capabilities: process_list={caps.has_process_list}, storage={caps.has_storage}, "
            f"network={caps.has_network}, gpu={caps.has_gpu}, sensors={caps.has_sensors}, "
            f"battery={caps.has_battery}"
        )
    else:
        print("\n  CRITICAL: No compatible driver found.")

    _report_scripts(engine.loader.active_scripts)

    print("\n  Config:")
    print(f"    theme={config.theme}, poll_interval_ms={config.poll_interval_ms}")
    print(f"    driver_override={config.driver_override}")
    print(f"    database_retention_days={config.database_retention_days}")

    print("\n=== Event Loop Started ===\n")
    try:
        for tick in range(5):
            state = engine.get_system_state()

            if "error" in state:
                print(f"ERROR: {state['error']}")
                break

            cpu = state["cpu"]
            ram = state["ram"]
            print(
                f"[{tick + 1}] CPU: {cpu['usage_percent']}% ({cpu['physical_cores']}C/{cpu['logical_cores']}T) "
                f"| RAM: {ram['percent']}% ({ram['used_bytes'] >> 20}MB / {ram['total_bytes'] >> 20}MB)"
            )

            procs = state.get("processes")
            if procs:
                top = sorted(procs, key=lambda p: p["cpu_percent"], reverse=True)[0]
                print(
                    f"     Top: PID {top['pid']} {top['name']} @ {top['cpu_percent']}%"
                )

            net = state.get("network")
            if net:
                n = net[0]
                print(
                    f"     Net: {n['bytes_sent'] >> 10}KB sent / {n['bytes_recv'] >> 10}KB recv"
                )

            gpu = state.get("gpu")
            if gpu:
                for g in gpu:
                    print(
                        f"     GPU: {g['name']} @ {g['usage_percent']}% "
                        f"({g['memory_used'] >> 20}MB / {g['memory_total'] >> 20}MB)"
                    )

            battery = state.get("battery")
            if battery:
                plugged = "plugged" if battery.get("power_plugged") else "on battery"
                print(f"     Battery: {battery['percent']}% ({plugged})")

            time.sleep(1)
    except KeyboardInterrupt:
        pass

    rows = db.query_range("2000-01-01", "2100-01-01")
    print(f"\n  DB entries: {len(rows)}")
    db.close()


if __name__ == "__main__":
    main()
