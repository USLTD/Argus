from PyQt6.QtWidgets import QWidget
from PyQt6.QtWidgets import QVBoxLayout

from frontend.ui.widgets.memory_bar import (
    MemoryBar
)

from frontend.graphs.memory_graph import (
    MemoryGraph
)

from frontend.core.engine_bridge import EngineBridge


class MemoryPage(QWidget):

    def __init__(self, bridge: EngineBridge | None = None) -> None:

        super().__init__()

        self._bridge: EngineBridge | None = bridge

        layout = QVBoxLayout(self)

        layout.addWidget(
            MemoryGraph()
        )

        layout.addWidget(
            MemoryBar(bridge=self._bridge)
        )

        layout.addWidget(
            MemoryBar(bridge=self._bridge)
        )

        layout.addWidget(
            MemoryBar(bridge=self._bridge)
        )

        layout.addWidget(
            MemoryBar(bridge=self._bridge)
        )