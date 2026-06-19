from PyQt6.QtWidgets import QWidget
from PyQt6.QtWidgets import QGridLayout

from frontend.graphs.cpu_graph import CPUGraph


class CPUPage(QWidget):

    def __init__(self):

        super().__init__()

        layout = QGridLayout(self)

        self.main_graph = CPUGraph()

        layout.addWidget(
            self.main_graph,
            0,
            0,
            1,
            4
        )

        self.core_graphs = []

        for i in range(8):

            graph = CPUGraph()

            self.core_graphs.append(
                graph
            )

            row = 1 + (i // 4)

            col = i % 4

            layout.addWidget(
                graph,
                row,
                col
            )