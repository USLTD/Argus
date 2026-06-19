from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar
)

from frontend.core.engine_bridge import bridge


class CPUPerCoreWidget(QWidget):

    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout(self)

        self.rows = []

        cores = bridge.get_cpu_metrics()["logical_cores"]

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

            self.layout.addLayout(row)

            self.rows.append(
                (
                    bar,
                    load_label,
                    avg_label,
                    temp_label
                )
            )

        self.update_stats()

    def update_stats(self):

        usage = bridge.get_cpu_metrics()["per_core"] or []

        for i, value in enumerate(usage):

            bar, load, avg, temp = self.rows[i]

            bar.setValue(int(value))

            load.setText(f"{value:.0f}%")

            avg.setText(f"{value/100:.2f}")

            temp.setText("--°C")