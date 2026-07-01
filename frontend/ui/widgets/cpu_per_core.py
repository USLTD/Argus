from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar

from backend.interfaces.contexts import BridgeContext
from frontend.core.engine_bridge import EngineBridge


class CPUPerCoreWidget(QWidget):
    def __init__(self, bridge: EngineBridge | None = None) -> None:
        super().__init__()

        self._bridge: EngineBridge | None = bridge

        self._core_layout = QVBoxLayout(self)  # type: ignore[assignment]

        self.rows = []

        cores = self._bridge.get_cpu_metrics()["logical_cores"] if self._bridge else 0

        for i in range(cores):
            row = QHBoxLayout()

            core_label = QLabel(f"Core {i}")

            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setTextVisible(False)

            load_label = QLabel("0%")
            avg_label = QLabel("0.00")
            temp_label = QLabel("--°C")

            row.addWidget(core_label)
            row.addWidget(bar, 1)
            row.addWidget(load_label)
            row.addWidget(avg_label)
            row.addWidget(temp_label)

            self._core_layout.addLayout(row)

            self.rows.append((bar, load_label, avg_label, temp_label))

        if self._bridge:
            self._bridge.state_updated.connect(self._on_state)

    def _on_state(self, ctx: BridgeContext) -> None:
        self.update_stats()

    def update_stats(self):

        usage = self._bridge.get_cpu_metrics()["per_core"] or []

        for i, value in enumerate(usage):
            bar, load, avg, temp = self.rows[i]

            bar.setValue(int(value))

            load.setText(f"{value:.0f}%")

            avg.setText(f"{value / 100:.2f}")

            temp.setText("--°C")
