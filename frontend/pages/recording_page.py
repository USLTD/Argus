from PyQt6.QtWidgets import (
    QPushButton,
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
    QSlider,
    QTableWidgetItem,
    QComboBox,
)

from PyQt6.QtCore import Qt, QTimer

from datetime import datetime, timedelta

from frontend.core.engine_bridge import EngineBridge
from frontend.pages.overview_page import OverviewPage


class RecordingPage(OverviewPage):
    """
    Time Machine page.

    Reuses OverviewPage:
        - CPU
        - CPU cores
        - Memory
        - Disk
        - Network
        - Processes
        - System Load

    Loads previous states from database.
    """

    def __init__(self, bridge: EngineBridge | None = None):

        super().__init__(bridge)

        self.live_mode = True

        # Disconnect inherited live handler and connect our own that checks live_mode
        try:
            self._bridge.state_updated.disconnect(self._on_state)
        except (TypeError, RuntimeError):
            pass
        self._bridge.state_updated.connect(self._on_tick_live)

        self.bridge = bridge

        self.current_time = datetime.now()

        self.playing = False

        self.timer = QTimer()

        self.timer.timeout.connect(self.go_forward)

        self.interval = 1000
        self.create_controls()

    # -------------------------------------------------
    # Controls
    # -------------------------------------------------

    def create_controls(self):

        root = QVBoxLayout()

        # ---------------- Timeline ----------------

        self.timeline = QSlider(Qt.Orientation.Horizontal)
        self.timeline.setRange(-300, 0)
        self.timeline.setValue(0)

        root.addWidget(self.timeline)

        controls = QHBoxLayout()

        self.back300 = QPushButton("◀5m")
        self.back60 = QPushButton("◀1m")
        self.back10 = QPushButton("◀10s")
        self.back1 = QPushButton("◀1s")

        self.play_button = QPushButton("▶")
        self.live_button = QPushButton("LIVE")

        self.forward1 = QPushButton("1s▶")
        self.forward10 = QPushButton("10s▶")
        self.forward60 = QPushButton("1m▶")
        self.forward300 = QPushButton("5m▶")

        self.speed = QComboBox()
        self.speed.addItems(["0.25x", "0.5x", "1x", "2x", "5x", "10x"])
        self.speed.setCurrentText("1x")

        self.time_label = QLabel()

        buttons = [
            self.back300,
            self.back60,
            self.back10,
            self.back1,
            self.play_button,
            self.live_button,
            self.forward1,
            self.forward10,
            self.forward60,
            self.forward300,
        ]

        for button in buttons:
            button.setFixedSize(60, 28)
            button.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    font-weight: bold;
                }

                QPushButton:hover {
                    background-color: #42A5F5;
                }

                QPushButton:pressed {
                    background-color: #1976D2;
                }
            """)
            controls.addWidget(button)

        self.speed.setFixedWidth(70)

        controls.addWidget(self.speed)
        controls.addStretch()
        controls.addWidget(self.time_label)

        root.addLayout(controls)

        container = QWidget()
        container.setLayout(root)

        layout = self.layout()

        if layout:
            layout.addWidget(container)
        # Signals

        self.back1.clicked.connect(lambda: self.jump_seconds(-1))
        self.back10.clicked.connect(lambda: self.jump_seconds(-10))
        self.back60.clicked.connect(lambda: self.jump_seconds(-60))
        self.back300.clicked.connect(lambda: self.jump_seconds(-300))

        self.forward1.clicked.connect(lambda: self.jump_seconds(1))
        self.forward10.clicked.connect(lambda: self.jump_seconds(10))
        self.forward60.clicked.connect(lambda: self.jump_seconds(60))
        self.forward300.clicked.connect(lambda: self.jump_seconds(300))

        self.play_button.clicked.connect(self.toggle_play)
        self.live_button.clicked.connect(self.go_live)

        self.speed.currentTextChanged.connect(self.change_speed)

        self.timeline.valueChanged.connect(self.timeline_changed)

        self.update_time_label()

    # -------------------------------------------------
    # Live mode
    # -------------------------------------------------

    def _on_tick_live(self, ctx):
        """Override the inherited live tick handler — skip updates when viewing history."""
        if not self.live_mode:
            return
        self._on_state(ctx)

    # -------------------------------------------------
    # Database loading
    # -------------------------------------------------

    def load_time(self):

        if self.bridge is None:
            return

        try:
            snapshot = self.bridge.get_history_snapshot(self.current_time.isoformat())
        except Exception as e:
            print(f"TM load_time error: {e}")
            return

        print("TIME MACHINE:", self.current_time, snapshot)

        if snapshot is None:
            return

        self.update_from_snapshot(snapshot)

        self.update_time_label()

    # -------------------------------------------------
    # Update widgets
    # -------------------------------------------------

    def update_from_snapshot(self, data):

        # --- CPU ---
        if "cpu" in data:
            cpu_section = data["cpu"]
            if isinstance(cpu_section, dict):
                try:
                    self.cpu.update_value(cpu_section.get("cpu_percent", 0))
                except Exception as e:
                    print(f"TM cpu update error: {e}")

                # --- Per-core CPU ---
                per_core = cpu_section.get("per_core")
                if per_core and isinstance(per_core, list):
                    for i, value in enumerate(per_core):
                        if i >= len(self.core_bars):
                            break
                        self.core_bars[i].setValue(int(value))
                        self.core_labels[i].setText(f"{value:.1f}%")
            else:
                try:
                    self.cpu.update_value(cpu_section)
                except Exception as e:
                    print(f"TM cpu update error: {e}")

        # --- Memory ---
        if "memory" in data and isinstance(data["memory"], dict):
            self.memory_bar.update_data(data["memory"])

        # --- Disk ---
        if (
            "disks" in data
            and isinstance(data.get("disks"), list)
            and len(data["disks"]) > 0
        ):
            disks = data["disks"]
            c_disk = disks[0]
            self.c_bar.setValue(int(c_disk.get("percent", 0)))
            self.c_label.setText(
                f"C: {c_disk.get('used', 0) / (1024**3):.0f} GB / {c_disk.get('total', 0) / (1024**3):.0f} GB"
            )
            if len(disks) > 1:
                d_disk = disks[1]
                self.d_bar.setValue(int(d_disk.get("percent", 0)))
                self.d_label.setText(
                    f"D: {d_disk.get('used', 0) / (1024**3):.0f} GB / {d_disk.get('total', 0) / (1024**3):.0f} GB"
                )

        # --- Network ---
        if "network" in data and isinstance(data["network"], dict):
            self.network_widget.update_data(data["network"])

        # --- Load / system stats ---
        if "load" in data and isinstance(data["load"], dict):
            ld = data["load"]
            self.load_cpu.setText(f"CPU Load: {ld.get('cpu_percent', 0):.1f}%")
            if "frequency" in ld:
                self.load_freq.setText(f"CPU Frequency: {ld['frequency']:.0f} MHz")
            self.load_processes.setText(f"Processes: {ld.get('processes', 0)}")
            self.load_threads.setText(f"Threads: {ld.get('threads', 0)}")
            self.load_handles.setText(f"Handles: {ld.get('handles', 0)}")

        # --- CPU frequency from cpu section (fallback if not in load) ---
        if "cpu" in data and isinstance(data["cpu"], dict):
            freq = data["cpu"].get("frequency")
            if freq is not None:
                self.load_freq.setText(f"CPU Frequency: {freq:.0f} MHz")

        # --- Processes ---
        if "processes" in data and isinstance(data["processes"], list):
            self.update_process_table_history(data["processes"])

    # -------------------------------------------------
    # Processes
    # -------------------------------------------------

    def update_process_table_history(self, processes):

        self.table.setRowCount(len(processes))

        for row, proc in enumerate(processes):
            values = [
                proc.get("pid", ""),
                proc.get("name", ""),
                proc.get("cpu_percent", ""),
                proc.get("memory_info", ""),
                proc.get("status", ""),
                proc.get("num_threads", ""),
            ]

            for col, value in enumerate(values):
                self.table.setItem(row, col, QTableWidgetItem(str(value)))

    # -------------------------------------------------
    # Timeline movement
    # -------------------------------------------------

    def go_back(self):

        self.live_mode = False

        self.current_time -= timedelta(seconds=1)

        self.timeline.setValue(self.timeline.value() - 1)

        self.load_time()

    def go_forward(self):

        self.live_mode = False

        self.current_time += timedelta(seconds=1)

        if self.current_time >= datetime.now():
            self.current_time = datetime.now()

        self.timeline.setValue(min(0, self.timeline.value() + 1))

        self.load_time()

    # -------------------------------------------------
    # Playback
    # -------------------------------------------------

    def toggle_play(self):

        self.playing = not self.playing

        if self.playing:
            self.play_button.setText("⏸ Pause")

            self.timer.start(self.interval)

        else:
            self.play_button.setText("▶ Play")

            self.timer.stop()

    # -------------------------------------------------
    # Live mode
    # -------------------------------------------------

    def go_live(self):

        self.live_mode = True

        self.current_time = datetime.now()

        self.timeline.setValue(0)

        # Refresh display with live data immediately
        self.update_cpu_cores()
        self.update_system_load()
        self.update_disks()
        self.update_processes()
        self.load_time()

    # -------------------------------------------------
    # Slider
    # -------------------------------------------------

    def timeline_changed(self, value):

        self.live_mode = False

        self.current_time = datetime.now() + timedelta(seconds=value)

        self.load_time()

    # -------------------------------------------------
    # Label
    # -------------------------------------------------

    def update_time_label(self):

        self.time_label.setText(self.current_time.strftime("%Y-%m-%d %H:%M:%S"))

    def jump_seconds(self, seconds):

        self.live_mode = False

        self.current_time += timedelta(seconds=seconds)

        if self.current_time > datetime.now():
            self.current_time = datetime.now()

        self.load_time()

    def change_speed(self, text):

        mapping = {
            "0.25x": 4000,
            "0.5x": 2000,
            "1x": 1000,
            "2x": 500,
            "5x": 200,
            "10x": 100,
        }

        self.interval = mapping[text]

        if self.playing:
            self.timer.start(self.interval)
