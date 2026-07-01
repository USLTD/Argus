from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QGroupBox,
    QLabel,
    QProgressBar,
)

from backend.interfaces.contexts import BridgeContext

from frontend.core.engine_bridge import EngineBridge

from frontend.graphs.cpu_graph import CPUGraph
from frontend.graphs.memory_graph import MemoryGraph
from frontend.graphs.disk_graph import DiskGraph
from frontend.graphs.network_graph import NetworkGraph


class PerformancePage(QWidget):

    def __init__(self, bridge: EngineBridge | None = None):

        super().__init__()

        self._bridge = bridge

        self.setStyleSheet("""
        QGroupBox{
            font-weight:bold;
            margin-top:8px;
        }

        QProgressBar{
            border:1px solid #bfc7d5;
            border-radius:4px;
            background:white;
            height:8px;
            text-align:center;
        }

        QProgressBar::chunk{
            background:#4A90E2;
            border-radius:4px;
        }
        """)

        main = QVBoxLayout(self)

        main.setContentsMargins(
            8,
            8,
            8,
            8
        )

        main.setSpacing(
            8
        )

        # =====================================================
        # LARGE CPU GRAPH
        # =====================================================

        cpu_box = QGroupBox(
            "CPU Performance"
        )

        cpu_layout = QVBoxLayout(cpu_box)

        self.cpu_graph = CPUGraph(
            bridge=self._bridge
        )

        self.cpu_graph.setMinimumHeight(
            220
        )

        cpu_layout.addWidget(
            self.cpu_graph
        )

        main.addWidget(
            cpu_box
        )

        # =====================================================
        # MEMORY + NETWORK
        # =====================================================

        middle = QHBoxLayout()

        memory_box = QGroupBox(
            "Memory"
        )

        memory_layout = QVBoxLayout(memory_box)

        self.memory_graph = MemoryGraph(
            bridge=self._bridge
        )

        self.memory_graph.setMinimumHeight(
            170
        )

        memory_layout.addWidget(
            self.memory_graph
        )

        middle.addWidget(
            memory_box
        )

        network_box = QGroupBox(
            "Network"
        )

        network_layout = QVBoxLayout(network_box)

        self.network_graph = NetworkGraph(
            bridge=self._bridge
        )

        self.network_graph.setMinimumHeight(
            170
        )

        network_layout.addWidget(
            self.network_graph
        )

        middle.addWidget(
            network_box
        )

        main.addLayout(
            middle
        )

        # =====================================================
        # DISK + CPU INFO
        # =====================================================

        bottom = QHBoxLayout()

        disk_box = QGroupBox(
            "Disk"
        )

        disk_layout = QVBoxLayout(disk_box)

        self.disk_graph = DiskGraph(
            "C:\\",
            bridge=self._bridge
        )

        self.disk_graph.setMinimumHeight(
            170
        )

        disk_layout.addWidget(
            self.disk_graph
        )

        bottom.addWidget(
            disk_box
        )

        info_box = QGroupBox(
            "CPU Information"
        )

        info_layout = QVBoxLayout(info_box)

        self.cpu_usage = QLabel("Usage:")
        self.cpu_freq = QLabel("Frequency:")
        self.cpu_cores = QLabel("Physical Cores:")
        self.cpu_threads = QLabel("Logical Cores:")

        info_layout.addWidget(self.cpu_usage)
        info_layout.addWidget(self.cpu_freq)
        info_layout.addWidget(self.cpu_cores)
        info_layout.addWidget(self.cpu_threads)
        info_layout.addStretch()

        bottom.addWidget(
            info_box
        )

        main.addLayout(
            bottom
        )

        # =====================================================
        # CPU CORE USAGE
        # =====================================================

        cores_box = QGroupBox(
            "CPU Core Usage"
        )

        cores_layout = QGridLayout(cores_box)

        self.core_bars = []
        self.core_labels = []

        if self._bridge:

            logical = self._bridge.get_cpu_metrics()[
                "logical_cores"
            ]

        else:

            logical = 8

        for i in range(logical):
            label = QLabel(
                f"Core {i}"
            )

            bar = QProgressBar()

            bar.setMaximum(100)

            value = QLabel(
                "0%"
            )

            row = i // 2
            col = (i % 2) * 3

            cores_layout.addWidget(
                label,
                row,
                col
            )

            cores_layout.addWidget(
                bar,
                row,
                col + 1
            )

            cores_layout.addWidget(
                value,
                row,
                col + 2
            )

            self.core_bars.append(bar)
            self.core_labels.append(value)

        main.addWidget(
            cores_box
        )

        if self._bridge:
            self._bridge.state_updated.connect(
                self.update_ui
            )


    def update_ui(self, ctx: BridgeContext) -> None:
        """
        Refresh every widget whenever EngineBridge emits state_updated.
        """

        if self._bridge is None:
            return

        # =====================================================
        # CPU
        # =====================================================

        cpu = self._bridge.get_cpu_metrics()

        self.cpu_usage.setText(
            f"Usage: {cpu['cpu_percent']:.1f}%"
        )

        freq = cpu["frequency"]

        if freq is None:
            self.cpu_freq.setText(
                "Frequency: N/A"
            )
        else:
            self.cpu_freq.setText(
                f"Frequency: {freq:.0f} MHz"
            )

        self.cpu_cores.setText(
            f"Physical Cores: {cpu['physical_cores']}"
        )

        self.cpu_threads.setText(
            f"Logical Cores: {cpu['logical_cores']}"
        )

        # =====================================================
        # CPU CORE BARS
        # =====================================================

        per_core = cpu["per_core"]

        for i, value in enumerate(per_core):

            if i >= len(self.core_bars):
                break

            self.core_bars[i].setValue(
                int(value)
            )

            self.core_labels[i].setText(
                f"{value:.0f}%"
            )




        # =====================================================
        # Refresh graphs
        # =====================================================

        self.cpu_graph.refresh()

        self.network_graph.refresh()

        self.disk_graph.refresh()