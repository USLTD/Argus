from PyQt6.QtWidgets import QWidget
from PyQt6.QtWidgets import QGridLayout

from frontend.graphs.cpu_graph import CPUGraph
from frontend.core.engine_bridge import EngineBridge


class CPUPage(QWidget):

    def __init__(self, bridge: EngineBridge | None = None) -> None:

        super().__init__()

        self._bridge: EngineBridge | None = bridge

        layout = QGridLayout(self)

        self.main_graph = CPUGraph(bridge=self._bridge)

        layout.addWidget(
            self.main_graph,
            0,
            0,
            1,
            4
        )

        self.core_graphs = []

        if self._bridge is not None:
            cpu = self._bridge.get_cpu_metrics()
            core_count = cpu.get("logical_cores", 0) or len(cpu.get("per_core", [])) or 8
        else:
            core_count = 8

        for i in range(core_count):

            graph = CPUGraph(bridge=self._bridge)

            self.core_graphs.append(
                graph
            )

            row = 1 + (i // 4)

            col = i % 4

            layout.addWidget(
                graph,
                row,
                col
            )