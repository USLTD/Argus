from frontend.graphs.base_graph import BaseGraph

from backend.interfaces.contexts import BridgeContext
from frontend.core.engine_bridge import EngineBridge


class MemoryGraph(BaseGraph):
    def __init__(self, bridge: EngineBridge | None = None) -> None:

        super().__init__("Memory Usage %")

        self._bridge: EngineBridge | None = bridge

        self.graph.setYRange(0, 100)

        if self._bridge:
            self._bridge.state_updated.connect(self._on_state)

    def _on_state(self, ctx: BridgeContext) -> None:
        self.refresh()

    def refresh(self) -> None:

        if self._bridge is None:
            return

        memory = self._bridge.get_memory_metrics()

        self.update_value(memory["percent"])
