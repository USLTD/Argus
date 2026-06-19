import pyqtgraph as pg

from PyQt6.QtWidgets import QWidget
from PyQt6.QtWidgets import QVBoxLayout


class BaseGraph(QWidget):

    def __init__(self, title):

        super().__init__()

        self.history = [0] * 60

        layout = QVBoxLayout(self)

        self.graph = pg.PlotWidget()

        layout.addWidget(self.graph)

        # =========================
        # STYLE (XP / Monitoring UI)
        # =========================

        self.graph.setBackground("w")  # white background

        self.graph.setTitle(title, color="black", size="10pt")

        self.graph.showGrid(x=True, y=True, alpha=0.2)

        self.graph.setMenuEnabled(False)

        self.graph.setMouseEnabled(x=True, y=True)

        # Axis styling
        self.graph.getAxis("left").setTextPen("black")
        self.graph.getAxis("bottom").setTextPen("black")

        # Light blue pen (main ARGUS style)
        self.pen = pg.mkPen(
            color=(120, 180, 255),
            width=2
        )

        # Optional subtle fill under graph (XP-like feel)
        self.brush = pg.mkBrush(120, 180, 255, 40)

        self.curve = self.graph.plot(
            self.history,
            pen=self.pen,
            fillLevel=0,
            brush=self.brush
        )

    def update_value(self, value):

        self.history.append(value)

        if len(self.history) > 60:
            self.history.pop(0)

        self.curve.setData(self.history)