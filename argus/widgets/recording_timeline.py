from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QSlider
)

from PyQt5.QtCore import Qt


class RecordingTimeline(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        self.label = QLabel(
            "Recording Timeline"
        )

        self.slider = QSlider(
            Qt.Horizontal
        )

        self.slider.setMaximum(
            3600
        )

        layout.addWidget(
            self.label
        )

        layout.addWidget(
            self.slider
        )