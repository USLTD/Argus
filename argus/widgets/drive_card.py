import random

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
    QProgressBar
)


class DriveCard(QFrame):

    def __init__(
            self,
            drive_name
    ):
        super().__init__()

        self.setObjectName("card")

        layout = QVBoxLayout(self)

        self.title = QLabel(
            drive_name
        )

        self.usage = QProgressBar()

        self.read = QLabel()
        self.write = QLabel()

        self.health = QLabel(
            "Health: Good"
        )

        self.temp = QLabel()

        layout.addWidget(
            self.title
        )

        layout.addWidget(
            self.usage
        )

        layout.addWidget(
            self.read
        )

        layout.addWidget(
            self.write
        )

        layout.addWidget(
            self.health
        )

        layout.addWidget(
            self.temp
        )

        self.timer = QTimer()

        self.timer.timeout.connect(
            self.update_data
        )

        self.timer.start(1000)

        self.update_data()

    def update_data(self):

        self.usage.setValue(
            random.randint(20,95)
        )

        self.read.setText(
            f"Read: {random.randint(50,900)} MB/s"
        )

        self.write.setText(
            f"Write: {random.randint(40,800)} MB/s"
        )

        self.temp.setText(
            f"Temperature: {random.randint(28,55)}°C"
        )