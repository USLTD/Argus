from PyQt6.QtWidgets import QLabel

from datetime import datetime

from PyQt6.QtCore import QTimer


class SystemClock(QLabel):

    def __init__(self):

        super().__init__()

        timer = QTimer(self)

        timer.timeout.connect(
            self.update_time
        )

        timer.start(1000)

        self.update_time()

    def update_time(self):

        self.setText(
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )