from PyQt6.QtWidgets import QWidget, QVBoxLayout

from frontend.graphs.network_graph import NetworkGraph
from frontend.ui.widgets.adapter_table import AdapterTable
from frontend.core.engine_bridge import EngineBridge


class NetworkPage(QWidget):

    def __init__(self, bridge: EngineBridge | None = None) -> None:
        super().__init__()

        self._bridge: EngineBridge | None = bridge

        # ✅ Create a layout instance
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        # ✅ Add widgets to the layout
        layout.addWidget(AdapterTable())
        layout.addWidget(NetworkGraph(bridge=self._bridge))
