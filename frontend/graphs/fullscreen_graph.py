from PyQt6.QtWidgets import QMainWindow


class FullscreenGraphWindow(
    QMainWindow
):

    def __init__(self, graph):

        super().__init__()

        self.setWindowTitle(
            "ARGUS Graph Viewer"
        )

        self.resize(1200, 700)

        self.setCentralWidget(graph)