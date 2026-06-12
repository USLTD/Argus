import random

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QWidget, QVBoxLayout

import pyqtgraph as pg


class GraphWidget(QWidget):

    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout(self)

        self.plot_widget = pg.PlotWidget()

        self.layout.addWidget(self.plot_widget)

        self.data = [random.randint(20, 60) for _ in range(60)]

        self.curve = self.plot_widget.plot(
            self.data,
            pen=pg.mkPen(width=2)
        )

        self.plot_widget.showGrid(x=True, y=True)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_graph)
        self.timer.start(1000)

    def update_graph(self):

        self.data.pop(0)

        last = self.data[-1]

        value = max(
            0,
            min(
                100,
                last + random.randint(-10, 10)
            )
        )

        self.data.append(value)

        self.curve.setData(self.data)