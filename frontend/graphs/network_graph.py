from frontend.graphs.base_graph import BaseGraph

from backend.interfaces.contexts import BridgeContext
from frontend.core.engine_bridge import EngineBridge, NetworkIODict


class NetworkGraph(BaseGraph):
    def __init__(self, bridge: EngineBridge | None = None) -> None:

        super().__init__("Network Activity (MB/s)")

        self._bridge: EngineBridge | None = bridge

        self.old_data: NetworkIODict = self._bridge.get_network_io()

        self.graph.setYRange(0, 10)

        if self._bridge:
            self._bridge.state_updated.connect(self._on_state)

    def _on_state(self, ctx: BridgeContext) -> None:
        self.refresh()

    def refresh(self):

        new_data = self._bridge.get_network_io()

        download = new_data["bytes_recv"] - self.old_data["bytes_recv"]

        self.old_data = new_data

        # convert bytes -> MB

        download_mb = download / (1024**2)

        # show download activity

        self.update_value(download_mb)
