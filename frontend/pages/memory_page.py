from PyQt6.QtWidgets import QWidget
from PyQt6.QtWidgets import QVBoxLayout

from frontend.ui.widgets.memory_bar import (
    MemoryBar
)

from frontend.graphs.memory_graph import (
    MemoryGraph
)


class MemoryPage(QWidget):

    def __init__(self):

        super().__init__()

        layout = QVBoxLayout(self)

        layout.addWidget(
            MemoryGraph()
        )

        layout.addWidget(
            MemoryBar()
        )

        layout.addWidget(
            MemoryBar()
        )

        layout.addWidget(
            MemoryBar()
        )

        layout.addWidget(
            MemoryBar()
        )