from PyQt5.QtWidgets import (
    QWidget,
    QGridLayout
)

from widgets.stat_card import (
    StatCard
)


class HistoryDashboard(QWidget):

    def __init__(self):
        super().__init__()

        layout = QGridLayout(self)

        metrics = [
            "CPU History",
            "RAM History",
            "Disk History",
            "Network History"
        ]

        for i,name in enumerate(metrics):

            layout.addWidget(
                StatCard(name),
                i // 2,
                i % 2
            )