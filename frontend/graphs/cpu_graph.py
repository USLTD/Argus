from frontend.graphs.base_graph import BaseGraph

from backend.interfaces.contexts import BridgeContext
from frontend.core.engine_bridge import EngineBridge


class CPUGraph(BaseGraph):
    def __init__(self, bridge: EngineBridge | None = None) -> None:

        super().__init__("CPU Usage %")

        self._bridge: EngineBridge | None = bridge

        if self._bridge:
            self._bridge.state_updated.connect(self._on_state)

    def _on_state(self, ctx: BridgeContext) -> None:
        self.refresh()

    def refresh(self):

        cpu = self._bridge.get_cpu_metrics()["cpu_percent"]

        self.update_value(cpu)
