from PyQt6.QtWidgets import (
    QPushButton,
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
    QSlider,
    QTableWidgetItem,
    QComboBox
)

from PyQt6.QtCore import (
    Qt,
    QTimer
)

from datetime import datetime, timedelta

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


    def __init__(self, bridge):

        super().__init__(
            bridge
        )


        self.bridge = bridge


        self.current_time = datetime.now()


        self.playing = False


        self.timer = QTimer()

        self.timer.timeout.connect(
            self.go_forward
        )

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
        self.speed.addItems([
            "0.25x",
            "0.5x",
            "1x",
            "2x",
            "5x",
            "10x"
        ])
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
            self.forward300
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

        self.layout().addWidget(
            container,
            3,
            0,
            1,
            3
        )
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

        self.speed.currentTextChanged.connect(
            self.change_speed
        )

        self.timeline.valueChanged.connect(
            self.timeline_changed
        )

        self.update_time_label()



    # -------------------------------------------------
    # Database loading
    # -------------------------------------------------

    def load_time(self):


        snapshot = self.bridge.get_history_snapshot(
            self.current_time.isoformat()
        )


        print(
            "TIME MACHINE:",
            self.current_time,
            snapshot
        )


        if snapshot is None:

            return


        self.update_from_snapshot(
            snapshot
        )


        self.update_time_label()



    # -------------------------------------------------
    # Update widgets
    # -------------------------------------------------

    def update_from_snapshot(
            self,
            data
    ):


        if "cpu" in data:

            try:

                self.cpu.update_data(
                    data["cpu"]
                )

            except Exception:

                pass



        if "memory" in data:

            try:

                self.memory_bar.update_data(
                    data["memory"]
                )

            except Exception:

                pass



        if "network" in data:

            try:

                self.network_widget.update_data(
                    data["network"]
                )

            except Exception:

                pass



        if "processes" in data:

            self.update_process_table_history(
                data["processes"]
            )



    # -------------------------------------------------
    # Processes
    # -------------------------------------------------

    def update_process_table_history(
            self,
            processes
    ):


        self.table.setRowCount(
            len(processes)
        )


        for row, proc in enumerate(processes):


            values = [

                proc.get("pid", ""),

                proc.get("name", ""),

                proc.get("cpu_percent", ""),

                proc.get("memory_info", ""),

                proc.get("status", ""),

                proc.get("num_threads", "")

            ]


            for col, value in enumerate(values):

                self.table.setItem(
                    row,
                    col,
                    QTableWidgetItem(
                        str(value)
                    )
                )



    # -------------------------------------------------
    # Timeline movement
    # -------------------------------------------------

    def go_back(self):

        self.current_time -= timedelta(
            seconds=1
        )


        self.timeline.setValue(
            self.timeline.value() - 1
        )


        self.load_time()



    def go_forward(self):

        self.current_time += timedelta(
            seconds=1
        )


        if self.current_time >= datetime.now():

            self.current_time = datetime.now()



        self.timeline.setValue(
            min(
                0,
                self.timeline.value() + 1
            )
        )


        self.load_time()



    # -------------------------------------------------
    # Playback
    # -------------------------------------------------

    def toggle_play(self):

        self.playing = not self.playing


        if self.playing:


            self.play_button.setText(
                "⏸ Pause"
            )


            self.timer.start(
                self.interval
            )


        else:


            self.play_button.setText(
                "▶ Play"
            )


            self.timer.stop()



    # -------------------------------------------------
    # Live mode
    # -------------------------------------------------

    def go_live(self):

        self.current_time = datetime.now()


        self.timeline.setValue(
            0
        )


        self.load_time()



    # -------------------------------------------------
    # Slider
    # -------------------------------------------------

    def timeline_changed(
            self,
            value
    ):


        self.current_time = (

            datetime.now()

            +

            timedelta(
                seconds=value
            )

        )


        self.load_time()



    # -------------------------------------------------
    # Label
    # -------------------------------------------------

    def update_time_label(self):

        self.time_label.setText(

            self.current_time.strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        )

    def jump_seconds(self, seconds):

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
            "10x": 100
        }

        self.interval = mapping[text]

        if self.playing:
            self.timer.start(
                self.interval
            )