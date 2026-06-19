from PyQt6.QtWidgets import QWidget, QVBoxLayout

from frontend.graphs.network_graph import NetworkGraph
from frontend.ui.widgets.adapter_table import AdapterTable


class NetworkPage(QWidget):

    def __init__(self):
        super().__init__()

        # ✅ Create a layout instance
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        # ✅ Add widgets to the layout
        layout.addWidget(AdapterTable())
        layout.addWidget(NetworkGraph())
