from PyQt6.QtWidgets import QDockWidget

from frontend.graphs.cpu_graph import CPUGraph


class SystemLoadDock(QDockWidget):

    def __init__(self):

        super().__init__(
            "System Load"
        )

        self.setWidget(
            CPUGraph()
        )