from PyQt5.QtWidgets import (
    QMainWindow
)

from widgets.graph_widget import (
    GraphWidget
)


class GraphWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle(
            "Graph Viewer"
        )

        self.resize(
            1200,
            700
        )

        self.setCentralWidget(
            GraphWidget()
        )