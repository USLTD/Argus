from PyQt6.QtWidgets import QWidget, QVBoxLayout

from frontend.graphs.network_graph import NetworkGraph
from frontend.ui.widgets.adapter_table import AdapterTable

from frontend.core.engine_bridge import EngineBridge



class NetworkPage(QWidget):

    def __init__(
        self,
        bridge: EngineBridge | None = None
    ) -> None:

        super().__init__()


        self._bridge = bridge


        layout = QVBoxLayout(
            self
        )


        #
        # Network adapters table
        #

        self.adapter_table = AdapterTable(
            bridge=self._bridge
        )

        layout.addWidget(
            self.adapter_table
        )



        #
        # Network traffic graph
        #

        self.network_graph = NetworkGraph(
            bridge=self._bridge
        )


        layout.addWidget(
            self.network_graph
        )