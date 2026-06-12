import random

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QGridLayout
)

from widgets.metric_card import MetricCard
from widgets.graph_widget import GraphWidget


class MemoryPage(QWidget):

    def __init__(self):

        super().__init__()

        root = QVBoxLayout(self)

        title = QLabel(
            "Memory Center"
        )

        title.setObjectName(
            "PageTitle"
        )

        root.addWidget(title)

        grid = QGridLayout()

        self.total = MetricCard(
            "Total RAM",
            "32",
            "GB"
        )

        self.used = MetricCard(
            "Used RAM",
            "18",
            "GB"
        )

        self.available = MetricCard(
            "Available",
            "14",
            "GB"
        )

        self.cached = MetricCard(
            "Cached",
            "8",
            "GB"
        )

        self.swap = MetricCard(
            "Swap",
            "2",
            "GB"
        )

        self.commit = MetricCard(
            "Commit",
            "24",
            "GB"
        )

        cards = [
            self.total,
            self.used,
            self.available,
            self.cached,
            self.swap,
            self.commit
        ]

        for i, card in enumerate(cards):

            grid.addWidget(
                card,
                i // 3,
                i % 3
            )

        root.addLayout(grid)

        self.graph = GraphWidget()

        root.addWidget(self.graph)

        self.timer = QTimer()

        self.timer.timeout.connect(
            self.update_stats
        )

        self.timer.start(2000)

    def update_stats(self):

        used = random.randint(
            12,
            30
        )

        self.used.set_value(
            used,
            "GB"
        )

        self.available.set_value(
            32 - used,
            "GB"
        )

        self.cached.set_value(
            random.randint(4,12),
            "GB"
        )

        self.swap.set_value(
            random.randint(0,8),
            "GB"
        )

        self.commit.set_value(
            random.randint(18,32),
            "GB"
        )