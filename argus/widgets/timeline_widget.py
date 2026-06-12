from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QSlider,
    QLabel
)


class TimelineWidget(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        self.position_label = QLabel(
            "00:00:00"
        )

        self.slider = QSlider(
            Qt.Horizontal
        )

        self.slider.setMinimum(0)
        self.slider.setMaximum(86400)

        layout.addWidget(
            self.position_label
        )

        layout.addWidget(
            self.slider
        )

        self.slider.valueChanged.connect(
            self.update_label
        )

    def update_label(
            self,
            value
    ):

        h = value // 3600
        m = (value % 3600) // 60
        s = value % 60

        self.position_label.setText(
            f"{h:02}:{m:02}:{s:02}"
        )