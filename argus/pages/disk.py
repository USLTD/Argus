from PyQt5.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QGridLayout,
    QTabWidget
)

from widgets.drive_card import DriveCard
from widgets.partition_table import PartitionTable
from widgets.graph_widget import GraphWidget


class DiskPage(QWidget):

    def __init__(self):
        super().__init__()

        root = QVBoxLayout(self)

        # Title
        title = QLabel("Disk Center")
        title.setObjectName("PageTitle")
        root.addWidget(title)

        # --- Tabs ---
        self.tabs = QTabWidget()

        # Overview tab with drive cards
        overview = QWidget()
        grid = QGridLayout(overview)

        drives = [
            "C:",
            "D:",
            "E:",
            "NVMe 1",
            "Backup SSD",
            "External USB"
        ]

        for i, drive in enumerate(drives):
            grid.addWidget(DriveCard(drive), i // 2, i % 2)

        self.tabs.addTab(overview, "Overview")

        # Partitions tab
        self.tabs.addTab(PartitionTable(), "Partitions")

        # SMART tab (placeholder)
        smart = QLabel("SMART Diagnostics Placeholder")
        self.tabs.addTab(smart, "SMART")

        # Performance tab
        perf = GraphWidget()
        self.tabs.addTab(perf, "Performance")

        root.addWidget(self.tabs)
