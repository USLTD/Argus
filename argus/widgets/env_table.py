from PyQt5.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QSplitter,
    QLineEdit,
    QGridLayout,
    QFrame,
    QTabWidget
)

from widgets.hardware_tree import HardwareTree
from widgets.info_panel import InfoPanel
from widgets.services_table import ServicesTable
from widgets.env_table import EnvironmentTable


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
        items = ["CPU", "GPU", "RAM", "Motherboard", "BIOS", "OS"]

        for i, name in enumerate(items):
            card = QFrame()
            card.setObjectName("card")

            layout = QVBoxLayout(card)
            layout.addWidget(QLabel(name))
            layout.addWidget(QLabel("Detected"))

            stats.addWidget(card, i // 3, i % 3)

        root.addLayout(stats)

        # --- Tabs ---
        self.tabs = QTabWidget()

        # Hardware tab with splitter
        splitter = QSplitter()
        self.tree = HardwareTree()
        self.info = InfoPanel()
        splitter.addWidget(self.tree)
        splitter.addWidget(self.info)
        splitter.setSizes([350, 900])
        self.tabs.addTab(splitter, "Hardware")

        # Services tab
        services = ServicesTable()
        self.tabs.addTab(services, "Services")

        # Environment tab
        env = EnvironmentTable()
        self.tabs.addTab(env, "Environment")

        # Devices tab (placeholder)
        devices = QLabel("Device Explorer")
        self.tabs.addTab(devices, "Devices")

        root.addWidget(self.tabs)

        # Connect signals
        self.tree.itemClicked.connect(self.item_selected)
        self.search.textChanged.connect(self.filter_tree)

    def item_selected(self, item):
        self.info.update_info(item.text(0))

    def filter_tree(self, text):
        text = text.lower()
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            item.setHidden(text not in item.text(0).lower())
