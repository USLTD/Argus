from PyQt5.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QGridLayout,
    QPushButton
)

from widgets.metric_card import (
    MetricCard
)

from widgets.recording_timeline import (
    RecordingTimeline
)


class RecordingPage(QWidget):

    def __init__(self):

        super().__init__()

        root = QVBoxLayout(self)

        title = QLabel(
            "Recording Center"
        )

        title.setObjectName(
            "PageTitle"
        )

        root.addWidget(title)

        stats = QGridLayout()

        self.status = MetricCard(
            "Status",
            "Idle"
        )

        self.duration = MetricCard(
            "Duration",
            "00:00:00"
        )

        self.fps = MetricCard(
            "FPS",
            "60"
        )

        self.storage = MetricCard(
            "Storage",
            "0 GB"
        )

        stats.addWidget(
            self.status,
            0,
            0
        )

        stats.addWidget(
            self.duration,
            0,
            1
        )

        stats.addWidget(
            self.fps,
            1,
            0
        )

        stats.addWidget(
            self.storage,
            1,
            1
        )

        root.addLayout(stats)

        self.timeline = (
            RecordingTimeline()
        )

        root.addWidget(
            self.timeline
        )

        self.start_btn = QPushButton(
            "Start"
        )

        self.pause_btn = QPushButton(
            "Pause"
        )

        self.stop_btn = QPushButton(
            "Stop"
        )

        self.export_btn = QPushButton(
            "Export"
        )

        root.addWidget(
            self.start_btn
        )

        root.addWidget(
            self.pause_btn
        )

        root.addWidget(
            self.stop_btn
        )

        root.addWidget(
            self.export_btn
        )