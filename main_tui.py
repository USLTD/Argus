"""
Argus TUI — Textual multi-screen system monitor.

Screens
-------
1  Overview   — dashboard stat boxes (CPU, RAM, Disk, Processes) + Network + Battery
2  CPU        — aggregate + per-core usage bars + frequency + temperature
3  Memory     — RAM breakdown (total / used / free / available)
4  Disk       — per-partition usage cards
5  Network    — upload / download rates + cumulative totals
6  Processes  — DataTable with search filter, terminate, kill
7  System     — static host / platform / CPU / RAM info
8  About      — version, keybindings, credits
9  Settings   — live runtime config editor
"""

from __future__ import annotations

import os
import platform as _platform
import string
import sys
import time

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.screen import Screen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    ProgressBar,
    Select,
    Static,
    Switch,
)

from backend.storage.config import SUBSYSTEM_NAMES

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _fmt_bytes(n: int | float) -> str:
    """Format bytes as human-readable (e.g. 8.2 GB)."""
    n = float(n)
    for unit in ("B", "KB", "MB", "GB", "TB", "PB"):
        if abs(n) < 1024.0:
            return f"{n:.1f} {unit}"
        n /= 1024.0
    return f"{n:.1f} PB"


def _fmt_speed(bps: float) -> str:
    """Format bytes/sec."""
    return _fmt_bytes(bps).rstrip("B") + "B/s" if bps >= 1 else "0 B/s"


def _fmt_freq(mhz: int | float | None) -> str:
    """Format CPU frequency."""
    if mhz is None:
        return "N/A"
    mhz = float(mhz)
    if mhz >= 1000:
        return f"{mhz / 1000:.2f} GHz"
    return f"{mhz:.0f} MHz"


def _fmt_seconds(secs: float | None) -> str:
    """Format seconds → human duration."""
    if secs is None or secs <= 0:
        return "N/A"
    h = int(secs // 3600)
    m = int((secs % 3600) // 60)
    return f"{h}h {m}m" if h else f"{m}m"


def _create_bridge(engine):
    """Instantiate the driver → AsyncBridge."""
    from backend.bridges.async_bridge import AsyncBridge

    driver = engine.loader.active_driver
    if driver is None:
        raise RuntimeError("No driver loaded")
    return AsyncBridge(driver=driver)


def _discover_mounts() -> list[str]:
    """Return available mount-point paths."""
    if sys.platform == "win32":
        drives: list[str] = []
        for letter in string.ascii_uppercase:
            path = f"{letter}:\\"
            if os.path.exists(path):
                drives.append(path)
        return drives or ["C:\\"]
    return ["/"]


# ---------------------------------------------------------------------------
# CSS theme
# ---------------------------------------------------------------------------

CSS = """
Screen {
    background: #1a1a2e;
}

Header {
    background: #16213e;
    color: #e94560;
    text-style: bold;
}

Footer {
    background: #16213e;
    color: #e0e0e0;
}

Static, Label {
    color: #e0e0e0;
}

/* ── Stat boxes (Overview) ───────────────────────────────────────── */
.stat-box {
    border: solid #0f3460;
    background: #16213e;
    padding: 1 2;
    margin: 1;
    width: 1fr;
    height: auto;
    min-width: 20;
}

.stat-title {
    color: #e94560;
    text-style: bold;
}

.stat-value {
    color: #00ff88;
    text-style: bold;
}

/* ── Section titles ──────────────────────────────────────────────── */
.section-title {
    color: #e94560;
    text-style: bold;
    padding: 1 2 0 2;
    margin: 0;
}

/* ── ProgressBars ────────────────────────────────────────────────── */
ProgressBar {
    margin: 0 2;
    height: 1;
}

ProgressBar > .bar {
    color: #e94560;
    background: #0f3460;
}

ProgressBar > .bar--percentage {
    color: #e94560;
}

ProgressBar.core-bar {
    margin: 0 0 0 1;
}

/* ── DataTable ───────────────────────────────────────────────────── */
DataTable {
    border: solid #0f3460;
    margin: 1;
    height: 1fr;
}

DataTable > .datatable--header {
    background: #0f3460;
    color: #e94560;
    text-style: bold;
}

DataTable > .datatable--cursor {
    background: #e94560;
    color: #1a1a2e;
}

/* ── Buttons ─────────────────────────────────────────────────────── */
Button {
    background: #0f3460;
    color: #e0e0e0;
    border: solid #0f3460;
    margin: 0 1;
}

Button:hover {
    background: #e94560;
    color: #1a1a2e;
}

Button:focus {
    background: #e94560;
    color: #1a1a2e;
}

/* ── Input ────────────────────────────────────────────────────────── */
Input {
    background: #16213e;
    color: #e0e0e0;
    border: solid #0f3460;
    margin: 0 2;
}

Input:focus {
    border: solid #e94560;
}

/* ── Info cards (Disk, System) ───────────────────────────────────── */
.info-card {
    border: solid #0f3460;
    background: #16213e;
    padding: 1 2;
    margin: 0 2 1 2;
}

.info-label {
    padding: 0 2;
}

/* ── Network panel ───────────────────────────────────────────────── */
#net-panel {
    border: solid #0f3460;
    padding: 1 2;
    margin: 1 2;
}

.net-label {
    padding: 0 0 0 2;
}

/* ── Process action bar ──────────────────────────────────────────── */
#proc-actions {
    height: 3;
    margin: 0 1 1 1;
}

/* ── Settings screen ────────────────────────────────────────────── */
.setting-section {
    margin-top: 1;
    text-style: underline;
    padding: 0 2;
}
"""

# ═══════════════════════════════════════════════════════════════════════════
# Screens
# ═══════════════════════════════════════════════════════════════════════════


# ── Overview ──────────────────────────────────────────────────────────────


class OverviewScreen(Screen):
    """Dashboard — 4 stat boxes + network + battery."""

    BINDINGS = [("r", "refresh", "Refresh")]

    def compose(self) -> ComposeResult:
        with Vertical():
            with Horizontal():
                yield Vertical(
                    Static("CPU", classes="stat-title"),
                    Static("", id="ov-cpu", classes="stat-value"),
                    classes="stat-box",
                )
                yield Vertical(
                    Static("RAM", classes="stat-title"),
                    Static("", id="ov-ram", classes="stat-value"),
                    classes="stat-box",
                )
                yield Vertical(
                    Static("DISK", classes="stat-title"),
                    Static("", id="ov-disk", classes="stat-value"),
                    classes="stat-box",
                )
                yield Vertical(
                    Static("PROCESSES", classes="stat-title"),
                    Static("", id="ov-procs", classes="stat-value"),
                    classes="stat-box",
                )
            yield Static("", id="ov-network")
            yield Static("", id="ov-battery")

    def on_mount(self) -> None:
        poll_ms = self.app.engine.config.poll_interval_ms  # type: ignore[union-attr]
        self.set_interval(max(poll_ms / 1000, 0.5), self._poll)
        self.set_timer(0, self._poll)

    async def _poll(self) -> None:
        try:
            data = await self.app.bridge.get_all()  # type: ignore[union-attr]
        except Exception:
            return

        # CPU
        cpu = data["cpu"]
        cpu_pct = cpu.get("cpu_percent", 0.0)
        freq = _fmt_freq(cpu.get("frequency"))
        self.query_one("#ov-cpu", Static).update(f"{cpu_pct:.1f}%\n{freq}")

        # RAM
        mem = data["memory"]
        m_total = mem.get("total", 0)
        m_used = mem.get("used", 0)
        m_pct = mem.get("percent", 0.0)
        self.query_one("#ov-ram", Static).update(
            f"{m_pct:.1f}%\n{_fmt_bytes(m_used)} / {_fmt_bytes(m_total)}"
        )

        # Disk (first mount)
        mounts = _discover_mounts()
        d_total = 0
        d_used = 0
        d_pct = 0.0
        if mounts:
            try:
                d = await self.app.bridge.get_disk_usage(mounts[0])  # type: ignore[union-attr]
            except Exception:
                d = {}
            d_total = d.get("total", 0)
            d_used = d.get("used", 0)
            d_pct = d.get("percent", 0.0)
        self.query_one("#ov-disk", Static).update(
            f"{d_pct:.1f}%\n{_fmt_bytes(d_used)} / {_fmt_bytes(d_total)}"
        )

        # Process count
        procs = data["processes"]
        self.query_one("#ov-procs", Static).update(str(len(procs)))

        # Network
        net = data["network"]
        sent = net.get("bytes_sent", 0)
        recv = net.get("bytes_recv", 0)
        self.query_one("#ov-network", Static).update(
            f"[b]Network[/b]\n  Sent: {_fmt_bytes(sent)}    Recv: {_fmt_bytes(recv)}"
        )

        # Battery
        bat = data["battery"]
        bat_pct = bat.get("percent", 0.0)
        plugged = bat.get("power_plugged")
        if bat_pct > 0 or plugged is not None:
            status_str = "Plugged In" if plugged else "On Battery"
            rem = _fmt_seconds(bat.get("seconds_left"))
            extra = f"  ({rem} remaining)" if not plugged and rem != "N/A" else ""
            self.query_one("#ov-battery", Static).update(
                f"[b]Battery[/b]  {bat_pct:.0f}%  ● {status_str}{extra}"
            )
        else:
            self.query_one("#ov-battery", Static).update("[b]Battery[/b]  N/A")

    async def action_refresh(self) -> None:
        await self._poll()


# ── CPU ────────────────────────────────────────────────────────────────────


class CPUScreen(Screen):
    """Aggregate + per-core CPU usage with frequency and temperature."""

    BINDINGS = [("r", "refresh", "Refresh")]

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("CPU Usage", classes="section-title")
            yield ProgressBar(total=100, id="cpu-agg-bar", show_percentage=True)
            yield Static("", id="cpu-freq", classes="info-label")
            yield Static("", id="cpu-cores", classes="info-label")
            yield Static("Per-Core Usage", classes="section-title")
            yield Vertical(id="cores-container")
            yield Static("Temperatures", classes="section-title")
            yield Static("", id="cpu-temps", classes="info-label")

    def on_mount(self) -> None:
        self._bars_mounted = False
        poll_ms = self.app.engine.config.poll_interval_ms  # type: ignore[union-attr]
        self.set_interval(max(poll_ms / 1000, 0.5), self._poll)
        self.set_timer(0, self._poll)

    async def _poll(self) -> None:
        try:
            data = await self.app.bridge.get_all()  # type: ignore[union-attr]
        except Exception:
            return

        cpu = data["cpu"]
        agg = cpu.get("cpu_percent", 0.0)
        freq = cpu.get("frequency")
        per_core: list[float] = cpu.get("per_core", [])
        phys = cpu.get("physical_cores", 0)
        logic = cpu.get("logical_cores", 0)

        self.query_one("#cpu-agg-bar", ProgressBar).progress = agg
        self.query_one("#cpu-freq", Static).update(
            f"Frequency: [bold]{_fmt_freq(freq)}[/bold]"
        )
        self.query_one("#cpu-cores", Static).update(
            f"Cores: {phys} physical / {logic} logical"
        )

        # Mount per-core bars once
        if not self._bars_mounted and per_core:
            self._bars_mounted = True
            container = self.query_one("#cores-container", Vertical)
            for i in range(len(per_core)):
                row = Horizontal(
                    Static(f"Core {i}:  "),
                    ProgressBar(
                        total=100,
                        id=f"core-bar-{i}",
                        classes="core-bar",
                        show_percentage=False,
                    ),
                )
                container.mount(row)

        # Update core bars
        for i, val in enumerate(per_core):
            try:
                self.query_one(f"#core-bar-{i}", ProgressBar).progress = val
            except Exception:
                pass

        # Temperatures
        sensors = data["sensors"]
        temps = sensors.get("temperatures", {})
        if temps:
            lines: list[str] = []
            for name, values in temps.items():
                vals = ", ".join(f"{v:.1f}°C" for v in values)
                lines.append(f"  {name}: {vals}")
            self.query_one("#cpu-temps", Static).update("\n".join(lines))
        else:
            self.query_one("#cpu-temps", Static).update("  No temperature data")

    async def action_refresh(self) -> None:
        await self._poll()


# ── Memory ─────────────────────────────────────────────────────────────────


class MemoryScreen(Screen):
    """RAM breakdown — total, used, free, available."""

    BINDINGS = [("r", "refresh", "Refresh")]

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("Memory Usage", classes="section-title")
            yield ProgressBar(total=100, id="mem-bar", show_percentage=True)
            yield Static("", id="mem-total", classes="info-label")
            yield Static("", id="mem-used", classes="info-label")
            yield Static("", id="mem-free", classes="info-label")
            yield Static("", id="mem-avail", classes="info-label")

    def on_mount(self) -> None:
        poll_ms = self.app.engine.config.poll_interval_ms  # type: ignore[union-attr]
        self.set_interval(max(poll_ms / 1000, 0.5), self._poll)
        self.set_timer(0, self._poll)

    async def _poll(self) -> None:
        try:
            data = await self.app.bridge.get_all()  # type: ignore[union-attr]
        except Exception:
            return

        mem = data["memory"]
        total = mem.get("total", 0)
        used = mem.get("used", 0)
        avail = mem.get("available", 0)
        free = mem.get("free", 0)
        pct = mem.get("percent", 0.0)

        self.query_one("#mem-bar", ProgressBar).progress = pct
        self.query_one("#mem-total", Static).update(f"  Total:     {_fmt_bytes(total)}")
        self.query_one("#mem-used", Static).update(
            f"  Used:      {_fmt_bytes(used)}  ({pct:.1f}%)"
        )
        self.query_one("#mem-free", Static).update(f"  Free:      {_fmt_bytes(free)}")
        self.query_one("#mem-avail", Static).update(f"  Available: {_fmt_bytes(avail)}")

    async def action_refresh(self) -> None:
        await self._poll()


# ── Disk ───────────────────────────────────────────────────────────────────


class DiskScreen(Screen):
    """Per-partition disk usage cards."""

    BINDINGS = [("r", "refresh", "Refresh")]

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("Disk Usage", classes="section-title")
            yield Vertical(id="disks-container")

    def on_mount(self) -> None:
        self._cards_mounted = False
        poll_ms = self.app.engine.config.poll_interval_ms  # type: ignore[union-attr]
        self.set_interval(max(poll_ms / 1000, 0.5), self._poll)
        self.set_timer(0, self._poll)

    async def _poll(self) -> None:
        mounts = _discover_mounts()
        disk_data: list[tuple[str, dict]] = []
        for m in mounts:
            try:
                d = await self.app.bridge.get_disk_usage(m)  # type: ignore[union-attr]
            except Exception:
                continue
            if d.get("total", 0) > 0:
                disk_data.append((m, d))

        container = self.query_one("#disks-container", Vertical)

        # Mount cards once
        if not self._cards_mounted and disk_data:
            self._cards_mounted = True
            for mount_path, d in disk_data:
                pct = d.get("percent", 0.0)
                used = d.get("used", 0)
                total = d.get("total", 0)
                label = mount_path.rstrip("\\").rstrip(":")
                card = Vertical(
                    Static(f"[bold]{label}[/bold]", classes="stat-title"),
                    ProgressBar(total=100, id=f"dk-bar-{label}", show_percentage=True),
                    Static(
                        f"  {_fmt_bytes(used)} / {_fmt_bytes(total)}  ({pct:.1f}%)",
                        id=f"dk-info-{label}",
                    ),
                    classes="info-card",
                )
                container.mount(card)

        # Update card values
        for mount_path, d in disk_data:
            pct = d.get("percent", 0.0)
            used = d.get("used", 0)
            total = d.get("total", 0)
            label = mount_path.rstrip("\\").rstrip(":")
            try:
                self.query_one(f"#dk-bar-{label}", ProgressBar).progress = pct
            except Exception:
                pass
            try:
                self.query_one(f"#dk-info-{label}", Static).update(
                    f"  {_fmt_bytes(used)} / {_fmt_bytes(total)}  ({pct:.1f}%)"
                )
            except Exception:
                pass

    async def action_refresh(self) -> None:
        await self._poll()


# ── Network ────────────────────────────────────────────────────────────────


class NetworkScreen(Screen):
    """Network throughput rates + cumulative totals."""

    BINDINGS = [("r", "refresh", "Refresh")]

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("Network I/O", classes="section-title")
            with Vertical(id="net-panel"):
                yield Static("", id="net-up", classes="net-label")
                yield Static("", id="net-down", classes="net-label")
                yield Static("", classes="net-label")
                yield Static("", id="net-tot-sent", classes="net-label")
                yield Static("", id="net-tot-recv", classes="net-label")

    def on_mount(self) -> None:
        self._prev_sent: int = 0
        self._prev_recv: int = 0
        self._prev_time: float = 0.0
        poll_ms = self.app.engine.config.poll_interval_ms  # type: ignore[union-attr]
        self.set_interval(max(poll_ms / 1000, 0.5), self._poll)
        self.set_timer(0, self._poll)

    async def _poll(self) -> None:
        try:
            data = await self.app.bridge.get_all()  # type: ignore[union-attr]
        except Exception:
            return

        net = data["network"]
        sent = net.get("bytes_sent", 0)
        recv = net.get("bytes_recv", 0)
        now = time.monotonic()

        if self._prev_time > 0:
            elapsed = now - self._prev_time
            if elapsed > 0:
                up_rate = max(sent - self._prev_sent, 0) / elapsed
                down_rate = max(recv - self._prev_recv, 0) / elapsed
            else:
                up_rate = 0.0
                down_rate = 0.0
        else:
            up_rate = 0.0
            down_rate = 0.0

        self.query_one("#net-up", Static).update(
            f"  Upload:   [bold]{_fmt_speed(up_rate)}[/bold]"
        )
        self.query_one("#net-down", Static).update(
            f"  Download: [bold]{_fmt_speed(down_rate)}[/bold]"
        )
        self.query_one("#net-tot-sent", Static).update(
            f"  Total Sent:   {_fmt_bytes(sent)}"
        )
        self.query_one("#net-tot-recv", Static).update(
            f"  Total Recv:   {_fmt_bytes(recv)}"
        )

        self._prev_sent = sent
        self._prev_recv = recv
        self._prev_time = now

    async def action_refresh(self) -> None:
        await self._poll()


# ── Processes ──────────────────────────────────────────────────────────────


class ProcessesScreen(Screen):
    """DataTable of processes with search filter, terminate, kill."""

    BINDINGS = [
        ("r", "refresh", "Refresh"),
        ("t", "terminate", "Terminate"),
        ("k", "kill", "Kill"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("Processes", classes="section-title")
            yield Input(placeholder="Search by name…", id="proc-search")
            yield DataTable(id="proc-table", cursor_type="row")
            with Horizontal(id="proc-actions"):
                yield Button("Terminate", id="btn-terminate", variant="warning")
                yield Button("Kill", id="btn-kill", variant="error")

    def on_mount(self) -> None:
        poll_ms = self.app.engine.config.poll_interval_ms  # type: ignore[union-attr]
        self.set_interval(max(poll_ms / 1000, 0.5), self._poll)
        self.set_timer(0, self._poll)

    async def _poll(self) -> None:
        try:
            data = await self.app.bridge.get_all()  # type: ignore[union-attr]
            processes = list(data["processes"])
        except Exception:
            processes = []

        query = self.query_one("#proc-search", Input).value.lower().strip()
        if query:
            processes = [p for p in processes if query in p.get("name", "").lower()]

        processes.sort(key=lambda p: p.get("cpu_percent", 0) or 0, reverse=True)

        table = self.query_one("#proc-table", DataTable)
        table.clear()
        table.add_columns("PID", "Name", "CPU%", "Mem", "Status")
        for p in processes[:200]:  # cap display
            pid = p.get("pid", 0)
            name = (p.get("name", "") or "?")[:40]
            cpu_pct = float(p.get("cpu_percent", 0) or 0)
            mem = int(p.get("memory_info", 0) or 0)
            status = (p.get("status", "") or "?")[:12]
            table.add_row(str(pid), name, f"{cpu_pct:.1f}", _fmt_bytes(mem), status)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        table = self.query_one("#proc-table", DataTable)
        if not table.row_count:
            return
        idx = table.cursor_row
        if idx < 0 or idx >= table.row_count:
            return
        try:
            row = table.get_row_at(idx)
            pid = int(row[0])
        except ValueError, IndexError:
            return

        if event.button.id == "btn-terminate":
            await self.app.bridge.terminate_process(pid)  # type: ignore[union-attr]
        elif event.button.id == "btn-kill":
            await self.app.bridge.kill_process(pid)  # type: ignore[union-attr]

    async def action_refresh(self) -> None:
        await self._poll()

    async def action_terminate(self) -> None:
        table = self.query_one("#proc-table", DataTable)
        if table.row_count and 0 <= table.cursor_row < table.row_count:
            try:
                pid = int(table.get_row_at(table.cursor_row)[0])
                await self.app.bridge.terminate_process(pid)  # type: ignore[union-attr]
            except ValueError, IndexError:
                pass

    async def action_kill(self) -> None:
        table = self.query_one("#proc-table", DataTable)
        if table.row_count and 0 <= table.cursor_row < table.row_count:
            try:
                pid = int(table.get_row_at(table.cursor_row)[0])
                await self.app.bridge.kill_process(pid)  # type: ignore[union-attr]
            except ValueError, IndexError:
                pass


def _fmt_info(val: object, fallback: str = "") -> str:
    """Format a static-info value, handling UnavailableInfo dicts."""
    if isinstance(val, dict) and val.get("unavailable") is True:
        reason = val.get("reason", "unknown")
        detail = val.get("detail", "")
        if detail:
            return f"[N/A: {reason} — {detail}]"
        return f"[N/A: {reason}]"
    if val is None:
        return fallback or "N/A"
    return str(val)


# ── System ─────────────────────────────────────────────────────────────────


class SystemScreen(Screen):
    """Static system information labels."""

    BINDINGS = [("r", "refresh", "Refresh")]

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("System Information", classes="section-title")
            yield Static("", id="sys-hostname", classes="info-label")
            yield Static("", id="sys-platform", classes="info-label")
            yield Static("", id="sys-cpu", classes="info-label")
            yield Static("", id="sys-cores", classes="info-label")
            yield Static("", id="sys-ram", classes="info-label")
            yield Static("", id="sys-python", classes="info-label")
            yield Static("", id="sys-arch", classes="info-label")
            yield Static("", id="sys-boot", classes="info-label")

    def on_mount(self) -> None:
        poll_ms = self.app.engine.config.poll_interval_ms  # type: ignore[union-attr]
        self.set_interval(max(poll_ms / 1000, 0.5), self._poll)
        self.set_timer(0, self._poll)

    async def _poll(self) -> None:
        try:
            info = await self.app.bridge.get_static_info()  # type: ignore[union-attr]
        except Exception:
            return

        if not isinstance(info, dict):
            return

        # System info
        system = info.get("system", {}) if isinstance(info, dict) else {}
        hostname = _fmt_info(system.get("hostname"), fallback=_platform.node())
        self.query_one("#sys-hostname", Static).update(f"  Hostname:  {hostname}")

        # OS info
        os_info = info.get("os", {}) if isinstance(info, dict) else {}
        plat = _fmt_info(os_info.get("name"), fallback=sys.platform)
        plat_ver = _fmt_info(os_info.get("version"), fallback=_platform.version())
        self.query_one("#sys-platform", Static).update(
            f"  Platform:  {plat} {plat_ver}"
        )

        # CPU info
        cpu = info.get("cpu", {}) if isinstance(info, dict) else {}
        cpu_brand = _fmt_info(cpu.get("name"), fallback=_platform.processor())
        self.query_one("#sys-cpu", Static).update(f"  CPU:       {cpu_brand}")

        phys_raw = cpu.get("physical_cores", 0)
        logic_raw = cpu.get("logical_cores", 0)
        phys = phys_raw if isinstance(phys_raw, int) else 0
        logic = logic_raw if isinstance(logic_raw, int) else 0
        self.query_one("#sys-cores", Static).update(
            f"  Cores:     {phys} physical / {logic} logical"
        )

        # Memory info
        memory = info.get("memory", {}) if isinstance(info, dict) else {}
        total_ram_raw = memory.get("total_ram_bytes", 0)
        total_ram = total_ram_raw if isinstance(total_ram_raw, (int, float)) else 0
        self.query_one("#sys-ram", Static).update(
            f"  RAM:       {_fmt_bytes(total_ram)}"
        )

        self.query_one("#sys-python", Static).update(
            f"  Python:    {sys.version.split()[0]}"
        )

        arch = _platform.machine()
        self.query_one("#sys-arch", Static).update(f"  Arch:      {arch}")

        try:
            bt = await self.app.bridge.get_boot_time()  # type: ignore[union-attr]
        except Exception:
            bt = 0.0
        if bt and bt > 0:
            boot_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(bt))
            self.query_one("#sys-boot", Static).update(f"  Boot:      {boot_str}")
        else:
            self.query_one("#sys-boot", Static).update("  Boot:      N/A")

    async def action_refresh(self) -> None:
        await self._poll()


# ── Settings ────────────────────────────────────────────────────────────────


class SettingsScreen(Screen):
    """Runtime config editor — edit ArgusConfig fields live."""

    BINDINGS = [("escape", "go_back", "Back"), ("r", "refresh", "Refresh")]

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("Settings", classes="section-title")
            yield Static("", id="settings-error")

            with ScrollableContainer():
                # ── Polling section ──
                yield Static("[bold]Polling[/bold]", classes="setting-section")
                yield Label("Poll interval (ms):")
                yield Input(
                    id="cfg-poll_interval_ms", type="integer", placeholder="1000"
                )
                yield Label("Process tick interval:")
                yield Input(
                    id="cfg-process_tick_interval", type="integer", placeholder="5"
                )
                yield Label("Driver override (empty = auto):")
                yield Input(id="cfg-driver_override", placeholder="")

                # ── Scripting section ──
                yield Static("[bold]Scripting[/bold]", classes="setting-section")
                yield Label("Script batch size:")
                yield Input(id="cfg-script_batch_size", type="integer", placeholder="4")
                yield Label("Script timeout (ms):")
                yield Input(
                    id="cfg-script_timeout_ms", type="integer", placeholder="5000"
                )
                yield Label("Execution mode:")
                yield Select(
                    id="cfg-script_execution_mode",
                    options=[
                        ("nonblocking", "nonblocking"),
                        ("blocking", "blocking"),
                        ("mixed", "mixed"),
                    ],
                    value="nonblocking",
                )
                yield Label("Compat default:")
                yield Select(
                    id="cfg-script_compatibility_default",
                    options=[("skip", "skip"), ("allow", "allow"), ("deny", "deny")],
                    value="skip",
                )

                # ── Subsystems section ──
                yield Static("[bold]Subsystems[/bold]", classes="setting-section")
                yield Label("Enable/disable and set intervals per subsystem:")
                for sub_name in SUBSYSTEM_NAMES:
                    with Horizontal():
                        yield Switch(id=f"cfg-subsystem_enabled-{sub_name}", value=True)
                        yield Label(f" {sub_name}")
                        yield Input(
                            id=f"cfg-subsystem_intervals-{sub_name}",
                            type="integer",
                            placeholder="1000",
                        )
                        yield Label("ms")

                # ── Buttons ──
                with Horizontal():
                    yield Button("Submit", id="btn-settings-submit", variant="primary")
                    yield Button(
                        "Reset to defaults", id="btn-settings-reset", variant="default"
                    )

    def on_mount(self) -> None:
        self._populate()

    def on_screen_resume(self) -> None:
        """Re-populate when screen becomes active (handles external config changes)."""
        self._populate()

    def _populate(self) -> None:
        config = self.app.engine.get_config()  # type: ignore[union-attr]
        for key, value in config.items():
            try:
                widget = self.query_one(f"#cfg-{key}")
            except Exception:
                continue
            if isinstance(widget, Select):
                widget.value = value
            elif isinstance(widget, Switch):
                widget.value = bool(value)
            elif isinstance(widget, Input):
                widget.value = str(value) if value is not None else ""

        # Subsystem enable switches
        for name in SUBSYSTEM_NAMES:
            try:
                sw = self.query_one(f"#cfg-subsystem_enabled-{name}", Switch)
                sw.value = bool(config.get("subsystem_enabled", {}).get(name, True))
            except Exception:
                pass

        # Subsystem interval inputs
        for name in SUBSYSTEM_NAMES:
            try:
                inp = self.query_one(f"#cfg-subsystem_intervals-{name}", Input)
                val = config.get("subsystem_intervals", {}).get(name, 1000)
                inp.value = str(val)
            except Exception:
                pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-settings-submit":
            self._save()
        elif event.button.id == "btn-settings-reset":
            self._reset()

    def _save(self) -> None:
        error_display = self.query_one("#settings-error", Static)
        error_display.update("")
        errors: list[str] = []

        # Simple scalar fields
        scalar_fields: dict[str, type] = {
            "poll_interval_ms": int,
            "process_tick_interval": int,
            "script_batch_size": int,
            "script_timeout_ms": int,
            "script_execution_mode": str,
            "script_compatibility_default": str,
            "driver_override": str,
        }
        for key, field_type in scalar_fields.items():
            try:
                widget = self.query_one(f"#cfg-{key}")
                if isinstance(widget, Select):
                    value = widget.value
                else:
                    raw = widget.value.strip()  # type: ignore[union-attr]
                    value = field_type(raw) if raw else None
                self.app.engine.set_config(key, value)  # type: ignore[union-attr]
            except Exception as e:
                errors.append(f"  {key}: {e}")

        # Subsystem enabled dict
        enabled: dict[str, bool] = {}
        for name in SUBSYSTEM_NAMES:
            try:
                sw = self.query_one(f"#cfg-subsystem_enabled-{name}", Switch)
                enabled[name] = sw.value
            except Exception as e:
                errors.append(f"  subsystem_enabled.{name}: {e}")
        try:
            self.app.engine.set_config("subsystem_enabled", enabled)  # type: ignore[union-attr]
        except Exception as e:
            errors.append(f"  subsystem_enabled: {e}")

        # Subsystem intervals dict
        intervals: dict[str, int] = {}
        for name in SUBSYSTEM_NAMES:
            try:
                inp = self.query_one(f"#cfg-subsystem_intervals-{name}", Input)
                raw = inp.value.strip()
                intervals[name] = int(raw) if raw else 1000
            except Exception as e:
                errors.append(f"  subsystem_intervals.{name}: {e}")
        try:
            self.app.engine.set_config("subsystem_intervals", intervals)  # type: ignore[union-attr]
        except Exception as e:
            errors.append(f"  subsystem_intervals: {e}")

        if errors:
            error_display.update("[red]Validation errors:[/red]\n" + "\n".join(errors))
        else:
            error_display.update("[green]Settings saved successfully![/green]")

    def _reset(self) -> None:
        from backend.storage.config import ArgusConfig

        defaults = ArgusConfig()
        for key in defaults.model_dump(mode="json"):
            if key in SUBSYSTEM_NAMES:
                continue  # Skip invalid keys
            try:
                self.app.engine.set_config(key, getattr(defaults, key))  # type: ignore[union-attr]
            except Exception:
                pass
        # Reset subsystem configs too
        self.app.engine.set_config("subsystem_enabled", defaults.subsystem_enabled)  # type: ignore[union-attr]
        self.app.engine.set_config("subsystem_intervals", defaults.subsystem_intervals)  # type: ignore[union-attr]
        self.app.engine.set_config("subsystem_timeout", defaults.subsystem_timeout)  # type: ignore[union-attr]
        self._populate()
        error_display = self.query_one("#settings-error", Static)
        error_display.update("[green]Settings reset to defaults![/green]")

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_refresh(self) -> None:
        self._populate()


# ── About ──────────────────────────────────────────────────────────────────


class AboutScreen(Screen):
    """App info, keybindings reference, credits."""

    BINDINGS = [("escape", "go_back", "Back"), ("r", "refresh", "Refresh")]

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("")
            yield Static(
                "            [bold #e94560]Argus TUI[/bold #e94560]",
                classes="section-title",
            )
            yield Static("")
            yield Static("            Powerful process manager for the terminal.")
            yield Static("")
            yield Static("            [bold]Keybindings[/bold]")
            yield Static("              1  —  Overview")
            yield Static("              2  —  CPU")
            yield Static("              3  —  Memory")
            yield Static("              4  —  Disk")
            yield Static("              5  —  Network")
            yield Static("              6  —  Processes")
            yield Static("              7  —  System")
            yield Static("              8  —  About")
            yield Static("              9  —  Settings")
            yield Static("              r  —  Refresh")
            yield Static("              q  —  Quit")
            yield Static("")
            yield Static("            [bold]Credits[/bold]")
            yield Static("            Built with Textual, psutil, and Pydantic.")
            yield Static("")
            yield Static("            [dim]Press ESC to go back.[/dim]")

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_refresh(self) -> None:
        pass  # Nothing to refresh


# ── Drivers ─────────────────────────────────────────────────────────────────


class DriverScreen(Screen):
    """Active driver info + all candidates with compatibility scores."""

    BINDINGS = [("escape", "go_back", "Back"), ("r", "refresh", "Refresh")]

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("Drivers", classes="section-title")
            yield Static("", id="drv-active")
            yield Static("", id="drv-candidates", classes="info-label")

    def on_mount(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        engine = self.app.engine  # type: ignore[union-attr]
        active_div = self.query_one("#drv-active", Static)
        driver = engine.loader.active_driver
        if driver:
            caps = driver.get_capabilities()
            active_div.update(
                f"  Active: [bold]{caps.driver.name}[/bold] "
                f"v{caps.driver.version} ([italic]{caps.driver.platform}[/italic])\n"
                f"    CPU={caps.cpu.present}, GPU={caps.gpu.present}, "
                f"Storage={caps.storage.present}, Network={caps.network.present}"
            )
        else:
            active_div.update("  [red]No active driver[/red]")

        # Show all candidates
        candidates_div = self.query_one("#drv-candidates", Static)
        active_name = (
            caps.driver.name
            if (driver and (caps := driver.get_capabilities()))
            else None
        )
        lines = ["  Candidates:"]
        for c in engine.list_drivers():
            tag = (
                "[green]ACTIVE[/green]"
                if c.get("name") == active_name
                else f"score={c['score']}"
            )
            lines.append(f"    {c['name']:20s} [{tag}]")
        candidates_div.update("\n".join(lines))

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_refresh(self) -> None:
        self._refresh()


# ── Scripts ─────────────────────────────────────────────────────────────────


class ScriptScreen(Screen):
    """List of loaded scripts with mode/permission info."""

    BINDINGS = [("escape", "go_back", "Back"), ("r", "refresh", "Refresh")]

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("Scripts", classes="section-title")
            yield Static("", id="scr-list", classes="info-label")

    def on_mount(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        engine = self.app.engine  # type: ignore[union-attr]
        scripts = engine.list_scripts()
        lines = [f"  Loaded: {len(scripts)}"]
        for s in scripts:
            lines.append(
                f"    {s['name']:20s} [{s['type']:6s}] mode={s['execution_mode']:12s}  "
                f"perms={len(s['permissions'])} events={len(s['hooked_events'])}"
            )
        if not scripts:
            lines.append("    (no scripts loaded)")
        self.query_one("#scr-list", Static).update("\n".join(lines))

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_refresh(self) -> None:
        self._refresh()


# ═══════════════════════════════════════════════════════════════════════════
# Application
# ═══════════════════════════════════════════════════════════════════════════


class ArgusTUI(App):
    """Multi-screen system monitor powered by Textual."""

    TITLE = "Argus TUI"
    CSS = CSS

    BINDINGS = [
        Binding("1", "show_overview", "Overview"),
        Binding("2", "show_cpu", "CPU"),
        Binding("3", "show_memory", "Memory"),
        Binding("4", "show_disk", "Disk"),
        Binding("5", "show_network", "Network"),
        Binding("6", "show_processes", "Processes"),
        Binding("7", "show_system", "System"),
        Binding("8", "show_about", "About"),
        Binding("9", "show_settings", "Settings"),
        Binding("d", "show_drivers", "Drivers"),
        Binding("s", "show_scripts", "Scripts"),
        Binding("r", "refresh", "Refresh"),
        Binding("q", "quit", "Quit"),
    ]

    SCREENS = {
        "overview": OverviewScreen,
        "cpu": CPUScreen,
        "memory": MemoryScreen,
        "disk": DiskScreen,
        "network": NetworkScreen,
        "processes": ProcessesScreen,
        "system": SystemScreen,
        "about": AboutScreen,
        "settings": SettingsScreen,
        "drivers": DriverScreen,
        "scripts": ScriptScreen,
    }

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()

    def __init__(self) -> None:
        super().__init__()
        from backend.core.engine import BackendEngine

        self.engine = BackendEngine()
        self.bridge = _create_bridge(self.engine)

    def on_mount(self) -> None:
        self.push_screen("overview")

    # ── Screen-switching actions ──────────────────────────────────────────

    def action_show_overview(self) -> None:
        self.push_screen("overview")

    def action_show_cpu(self) -> None:
        self.push_screen("cpu")

    def action_show_memory(self) -> None:
        self.push_screen("memory")

    def action_show_disk(self) -> None:
        self.push_screen("disk")

    def action_show_network(self) -> None:
        self.push_screen("network")

    def action_show_processes(self) -> None:
        self.push_screen("processes")

    def action_show_system(self) -> None:
        self.push_screen("system")

    def action_show_about(self) -> None:
        self.push_screen("about")

    def action_show_settings(self) -> None:
        self.push_screen("settings")

    def action_show_drivers(self) -> None:
        self.push_screen("drivers")

    def action_show_scripts(self) -> None:
        self.push_screen("scripts")

    async def action_refresh(self) -> None:
        """Force a bridge tick and re-poll the current screen."""
        try:
            await self.bridge.tick_all()
        except Exception:
            return
        screen = self.screen
        if screen is not None and hasattr(screen, "_poll"):
            await screen._poll()  # type: ignore[union-attr]


# ═══════════════════════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = ArgusTUI()
    app.run()
