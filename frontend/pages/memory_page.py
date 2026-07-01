from PyQt6.QtWidgets import QWidget, QVBoxLayout

from frontend.ui.widgets.memory_bar import MemoryBar
from frontend.graphs.memory_graph import MemoryGraph
from frontend.core.engine_bridge import EngineBridge


class MemoryPage(QWidget):
    def __init__(self, bridge: EngineBridge | None = None):

        super().__init__()

        self._bridge = bridge

        layout = QVBoxLayout(self)

        self.memory_graph = MemoryGraph(bridge=self._bridge)

        self.memory_bar = MemoryBar(bridge=self._bridge)

        layout.addWidget(self.memory_graph)
        layout.addWidget(self.memory_bar)
        layout.addStretch()
