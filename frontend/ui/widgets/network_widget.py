from PyQt6.QtWidgets import QWidget, QVBoxLayout

from frontend.graphs.base_graph import BaseGraph

from backend.interfaces.contexts import BridgeContext
from frontend.core.engine_bridge import EngineBridge, NetworkIODict


class NetworkWidget(QWidget):
    def __init__(self, bridge: EngineBridge | None = None) -> None:

        super().__init__()

        self._bridge: EngineBridge | None = bridge

        layout = QVBoxLayout(self)

        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self.download_graph = BaseGraph("Download MB/s")

        self.download_graph.setFixedHeight(65)

        layout.addWidget(self.download_graph)

        self.upload_graph = BaseGraph("Upload MB/s")

        self.upload_graph.setFixedHeight(65)

        layout.addWidget(self.upload_graph)

        if self._bridge:
            self._bridge.state_updated.connect(self._on_state)

    def _on_state(self, ctx: BridgeContext) -> None:
        net = ctx.data.get("network", {})
        if isinstance(net, dict):
            self.update_data(net)

    def update_data(self, data: NetworkIODict) -> None:
        self.download_graph.update_value(data.get("bytes_recv", 0) / (1024**2))
        self.upload_graph.update_value(data.get("bytes_sent", 0) / (1024**2))
