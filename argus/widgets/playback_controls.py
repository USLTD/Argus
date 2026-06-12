from PyQt5.QtWidgets import (
    QWidget,
    QPushButton,
    QHBoxLayout,
    QComboBox
)


class PlaybackControls(QWidget):

    def __init__(self):
        super().__init__()

        layout = QHBoxLayout(self)

        self.backward = QPushButton(
            "⏮"
        )

        self.play = QPushButton(
            "▶"
        )

        self.pause = QPushButton(
            "⏸"
        )

        self.forward = QPushButton(
            "⏭"
        )

        self.speed = QComboBox()

        self.speed.addItems([
            "0.25x",
            "0.5x",
            "1x",
            "2x",
            "4x",
            "8x"
        ])

        layout.addWidget(
            self.backward
        )

        layout.addWidget(
            self.play
        )

        layout.addWidget(
            self.pause
        )

        layout.addWidget(
            self.forward
        )

        layout.addWidget(
            self.speed
        )

        layout.addStretch()
        