from PyQt6.QtWidgets import QDockWidget

from frontend.core.engine_bridge import EngineBridge
from frontend.graphs.cpu_graph import CPUGraph


class SystemLoadDock(QDockWidget):

    def __init__(self, bridge: EngineBridge | None = None):

        super().__init__(
            "System Load"
        )

        self.setWidget(
            CPUGraph(bridge=bridge)
        )