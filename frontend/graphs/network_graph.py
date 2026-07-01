from frontend.graphs.base_graph import BaseGraph

from backend.interfaces.contexts import BridgeContext
from frontend.core.engine_bridge import EngineBridge


class NetworkGraph(BaseGraph):
    def __init__(self, bridge: EngineBridge | None = None) -> None:

        super().__init__("Network Activity (MB/s)")

        self._bridge: EngineBridge | None = bridge

        self.graph.setYRange(0, 10)

        if self._bridge:
            self._bridge.state_updated.connect(self._on_state)

    def _on_state(self, ctx: BridgeContext) -> None:
        net = ctx.data.get("network", {})
        if isinstance(net, dict):
            self.refresh(net)

    def refresh(self, net_data):
        download_mb = net_data.get("bytes_recv", 0) / (1024**2)
        self.update_value(download_mb)
