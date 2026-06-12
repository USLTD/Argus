from PyQt5.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QLineEdit,
    QGridLayout,
    QFrame
)

from widgets.hardware_tree import HardwareTree
from widgets.info_panel import InfoPanel


class SystemPage(QWidget):

    def __init__(self):
        super().__init__()

        root = QVBoxLayout(self)

        # Title
        title = QLabel("System Information")
        title.setObjectName("PageTitle")
        root.addWidget(title)

        # Search bar
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search hardware...")
        root.addWidget(self.search)

        # --- Overview cards ---
        stats = QGridLayout()

        items = [
            "CPU",
            "GPU",
            "RAM",
            "Motherboard",
            "BIOS",
            "OS"
        ]

        for i, name in enumerate(items):
            card = QFrame()
            card.setObjectName("card")

            layout = QVBoxLayout(card)
            layout.addWidget(QLabel(name))
            layout.addWidget(QLabel("Detected"))

            stats.addWidget(card, i // 3, i % 3)

        root.addLayout(stats)

        # --- Splitter with tree + info panel ---
        splitter = QSplitter()

        self.tree = HardwareTree()
        self.info = InfoPanel()

        splitter.addWidget(self.tree)
        splitter.addWidget(self.info)

        splitter.setSizes([350, 900])
        root.addWidget(splitter)

        # Connect tree clicks
        self.tree.itemClicked.connect(self.item_selected)

    def item_selected(self, item):
        self.info.update_info(item.text(0))
