from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem
)


class RecordingPage(QWidget):

    def __init__(self):

        super().__init__()

        layout = QVBoxLayout(self)

        self.status = QLabel(
            "Status: Idle"
        )

        self.duration = QLabel(
            "Duration: 00:00:00"
        )

        self.resolution = QLabel(
            "Resolution: 1920x1080"
        )

        self.fps = QLabel(
            "FPS: 60"
        )

        layout.addWidget(self.status)
        layout.addWidget(self.duration)
        layout.addWidget(self.resolution)
        layout.addWidget(self.fps)

        buttons = QHBoxLayout()

        for name in [
            "Record",
            "Pause",
            "Stop",
            "Export"
        ]:

            buttons.addWidget(
                QPushButton(name)
            )

        layout.addLayout(buttons)

        history = QTableWidget()

        history.setColumnCount(4)

        history.setHorizontalHeaderLabels(
            [
                "Date",
                "Duration",
                "Size",
                "Output"
            ]
        )

        history.setRowCount(10)

        for row in range(10):

            history.setItem(
                row,
                0,
                QTableWidgetItem(
                    "2026-01-01"
                )
            )

        layout.addWidget(history)