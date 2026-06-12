import random

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout
)

import pyqtgraph as pg


class TrafficGraph(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        self.graph = pg.PlotWidget()

        layout.addWidget(
            self.graph
        )

        self.download = [
            random.randint(10,50)
            for _ in range(60)
        ]

        self.upload = [
            random.randint(1,15)
            for _ in range(60)
        ]

        self.down_curve = self.graph.plot(
            self.download,
            pen=pg.mkPen(width=2)
        )

        self.up_curve = self.graph.plot(
            self.upload,
            pen=pg.mkPen(width=2)
        )

        self.timer = QTimer()

        self.timer.timeout.connect(
            self.update_data
        )

        self.timer.start(1000)

    def update_data(self):

        self.download.pop(0)
        self.upload.pop(0)

        self.download.append(
            random.randint(10,100)
        )

        self.upload.append(
            random.randint(1,50)
        )

        self.down_curve.setData(
            self.download
        )

        self.up_curve.setData(
            self.upload
        )