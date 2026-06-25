from frontend.graphs.base_graph import BaseGraph

from backend.interfaces.contexts import BridgeContext
from frontend.core.engine_bridge import EngineBridge


class DiskGraph(BaseGraph):

    def __init__(self, drive: str, bridge: EngineBridge | None = None) -> None:

        self.drive = drive
        self._bridge: EngineBridge | None = bridge

        title = f"{drive.replace(':\\\\', '')} Usage"

        super().__init__(title)

        self.graph.setYRange(0, 100)

        if self._bridge:
            self._bridge.state_updated.connect(self._on_state)

    def _on_state(self, ctx: BridgeContext) -> None:
        self.refresh()

    def refresh(self):

        try:
            percent = self._bridge.get_disk_usage(
                self.drive
            )["percent"]

            self.update_value(percent)

        except Exception:
            pass