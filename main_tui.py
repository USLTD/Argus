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
"""

from __future__ import annotations

import os
import platform as _platform
import string
import sys
import time

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, DataTable, Footer, Header, Input, ProgressBar, Static

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


def _create_bridge():
    """Instantiate the backend engine & driver → SyncBridge."""
    from backend.core.engine import BackendEngine
    from backend.bridges.sync_bridge import SyncBridge

    engine = BackendEngine()
    driver = engine.loader.active_driver
    if driver is None:
        raise RuntimeError("No driver loaded")
    return SyncBridge(driver=driver)


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
        self.set_interval(2, self._poll)
        self._poll()

    def _poll(self) -> None:
        try:
            self.app.bridge.tick_all()  # type: ignore[union-attr]
        except Exception:
            return

        # CPU
        cpu = self.app.bridge.get_cpu_metrics()  # type: ignore[union-attr]
        cpu_pct = cpu.get("cpu_percent", 0.0)
        freq = _fmt_freq(cpu.get("frequency"))
        self.query_one("#ov-cpu", Static).update(f"{cpu_pct:.1f}%\n{freq}")

        # RAM
        mem = self.app.bridge.get_memory_metrics()  # type: ignore[union-attr]
        m_total = mem.get("total", 0)
        m_used = mem.get("used", 0)
        m_pct = mem.get("percent", 0.0)
        self.query_one("#ov-ram", Static).update(
            f"{m_pct:.1f}%\n{_fmt_bytes(m_used)} / {_fmt_bytes(m_total)}"
        )

        # Disk
        mounts = _discover_mounts()
        d_total = 0
        d_used = 0
        d_pct = 0.0
        if mounts:
            d = self.app.bridge.get_disk_usage(mounts[0])  # type: ignore[union-attr]
            d_total = d.get("total", 0)
            d_used = d.get("used", 0)
            d_pct = d.get("percent", 0.0)
        self.query_one("#ov-disk", Static).update(
            f"{d_pct:.1f}%\n{_fmt_bytes(d_used)} / {_fmt_bytes(d_total)}"
        )

        # Process count
        procs = self.app.bridge.get_process_list()  # type: ignore[union-attr]
        self.query_one("#ov-procs", Static).update(str(len(procs)))

        # Network
        net = self.app.bridge.get_network_io()  # type: ignore[union-attr]
        sent = net.get("bytes_sent", 0)
        recv = net.get("bytes_recv", 0)
        self.query_one("#ov-network", Static).update(
            "[b]Network[/b]\n"
            f"  Sent: {_fmt_bytes(sent)}    "
            f"Recv: {_fmt_bytes(recv)}"
        )

        # Battery
        bat = self.app.bridge.get_battery()  # type: ignore[union-attr]
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

    def action_refresh(self) -> None:
        self._poll()


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
        self.set_interval(2, self._poll)
        self._poll()

    def _poll(self) -> None:
        try:
            self.app.bridge.tick_all()  # type: ignore[union-attr]
        except Exception:
            return

        cpu = self.app.bridge.get_cpu_metrics()  # type: ignore[union-attr]
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
                    ProgressBar(total=100, id=f"core-bar-{i}", classes="core-bar", show_percentage=False),
                )
                container.mount(row)

        # Update core bars
        for i, val in enumerate(per_core):
            try:
                self.query_one(f"#core-bar-{i}", ProgressBar).progress = val
            except Exception:
                pass

        # Temperatures
        sensors = self.app.bridge.get_sensors()  # type: ignore[union-attr]
        temps = sensors.get("temperatures", {})
        if temps:
            lines: list[str] = []
            for name, values in temps.items():
                vals = ", ".join(f"{v:.1f}°C" for v in values)
                lines.append(f"  {name}: {vals}")
            self.query_one("#cpu-temps", Static).update("\n".join(lines))
        else:
            self.query_one("#cpu-temps", Static).update("  No temperature data")

    def action_refresh(self) -> None:
        self._poll()


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
        self.set_interval(2, self._poll)
        self._poll()

    def _poll(self) -> None:
        try:
            self.app.bridge.tick_all()  # type: ignore[union-attr]
        except Exception:
            return

        mem = self.app.bridge.get_memory_metrics()  # type: ignore[union-attr]
        total = mem.get("total", 0)
        used = mem.get("used", 0)
        avail = mem.get("available", 0)
        free = mem.get("free", 0)
        pct = mem.get("percent", 0.0)

        self.query_one("#mem-bar", ProgressBar).progress = pct
        self.query_one("#mem-total", Static).update(f"  Total:     {_fmt_bytes(total)}")
        self.query_one("#mem-used", Static).update(f"  Used:      {_fmt_bytes(used)}  ({pct:.1f}%)")
        self.query_one("#mem-free", Static).update(f"  Free:      {_fmt_bytes(free)}")
        self.query_one("#mem-avail", Static).update(f"  Available: {_fmt_bytes(avail)}")

    def action_refresh(self) -> None:
        self._poll()


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
        self.set_interval(2, self._poll)
        self._poll()

    def _poll(self) -> None:
        try:
            self.app.bridge.tick_all()  # type: ignore[union-attr]
        except Exception:
            return

        mounts = _discover_mounts()
        disk_data: list[tuple[str, dict]] = []
        for m in mounts:
            d = self.app.bridge.get_disk_usage(m)  # type: ignore[union-attr]
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

    def action_refresh(self) -> None:
        self._poll()


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
        self.set_interval(2, self._poll)
        self._poll()

    def _poll(self) -> None:
        try:
            self.app.bridge.tick_all()  # type: ignore[union-attr]
        except Exception:
            return

        net = self.app.bridge.get_network_io()  # type: ignore[union-attr]
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

    def action_refresh(self) -> None:
        self._poll()


# ── Processes ──────────────────────────────────────────────────────────────


class ProcessesScreen(Screen):
    """DataTable of processes with search filter, terminate, kill."""

    BINDINGS = [("r", "refresh", "Refresh")]

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("Processes", classes="section-title")
            yield Input(placeholder="Search by name…", id="proc-search")
            yield DataTable(id="proc-table", cursor_type="row")
            with Horizontal(id="proc-actions"):
                yield Button("Terminate", id="btn-terminate", variant="warning")
                yield Button("Kill", id="btn-kill", variant="error")

    def on_mount(self) -> None:
        self.set_interval(2, self._poll)
        self._poll()

    def _poll(self) -> None:
        try:
            self.app.bridge.tick_all()  # type: ignore[union-attr]
            processes = list(self.app.bridge.get_process_list())  # type: ignore[union-attr]
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

    def on_button_pressed(self, event: Button.Pressed) -> None:
        table = self.query_one("#proc-table", DataTable)
        if not table.row_count:
            return
        idx = table.cursor_row
        if idx < 0 or idx >= table.row_count:
            return
        try:
            row = table.get_row_at(idx)
            pid = int(row[0])
        except (ValueError, IndexError):
            return

        if event.button.id == "btn-terminate":
            self.app.bridge.terminate_process(pid)  # type: ignore[union-attr]
        elif event.button.id == "btn-kill":
            self.app.bridge.kill_process(pid)  # type: ignore[union-attr]

    def action_refresh(self) -> None:
        self._poll()


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
        self.set_interval(2, self._poll)
        self._poll()

    def _poll(self) -> None:
        try:
            self.app.bridge.tick_all()  # type: ignore[union-attr]
        except Exception:
            pass

        info = self.app.bridge.get_static_info()  # type: ignore[union-attr]

        hostname = info.get("hostname") or _platform.node()
        self.query_one("#sys-hostname", Static).update(f"  Hostname:  {hostname}")

        plat = info.get("platform") or sys.platform
        plat_ver = info.get("platform_version") or _platform.version()
        self.query_one("#sys-platform", Static).update(
            f"  Platform:  {plat} {plat_ver}"
        )

        cpu_brand = info.get("cpu_brand") or _platform.processor()
        self.query_one("#sys-cpu", Static).update(f"  CPU:       {cpu_brand}")

        phys = info.get("cpu_physical_cores", 0)
        logic = info.get("cpu_logical_cores", 0)
        self.query_one("#sys-cores", Static).update(
            f"  Cores:     {phys} physical / {logic} logical"
        )

        total_ram = info.get("total_ram", 0)
        self.query_one("#sys-ram", Static).update(f"  RAM:       {_fmt_bytes(total_ram)}")

        self.query_one("#sys-python", Static).update(
            f"  Python:    {sys.version.split()[0]}"
        )

        arch = _platform.machine()
        self.query_one("#sys-arch", Static).update(f"  Arch:      {arch}")

        bt = self.app.bridge.get_boot_time()  # type: ignore[union-attr]
        if bt and bt > 0:
            boot_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(bt))
            self.query_one("#sys-boot", Static).update(f"  Boot:      {boot_str}")
        else:
            self.query_one("#sys-boot", Static).update("  Boot:      N/A")

    def action_refresh(self) -> None:
        self._poll()


# ── About ──────────────────────────────────────────────────────────────────


class AboutScreen(Screen):
    """App info, keybindings reference, credits."""

    BINDINGS = [("escape", "go_back", "Back"), ("r", "refresh", "Refresh")]

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("")
            yield Static("            [bold #e94560]Argus TUI[/bold #e94560]", classes="section-title")
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


# ═══════════════════════════════════════════════════════════════════════════
# Application
# ═══════════════════════════════════════════════════════════════════════════


class ArgusTUI(App):
    """8-screen system monitor powered by Textual."""

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
    }

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()

    def __init__(self) -> None:
        super().__init__()
        self.bridge = _create_bridge()

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

    def action_refresh(self) -> None:
        """Force a bridge tick and re-poll the current screen."""
        try:
            self.bridge.tick_all()
        except Exception:
            return
        screen = self.screen
        if screen is not None and hasattr(screen, "_poll"):
            screen._poll()  # type: ignore[union-attr]


# ═══════════════════════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = ArgusTUI()
    app.run()
