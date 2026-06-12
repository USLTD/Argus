from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QScrollArea,
    QGridLayout,
    QFrame,
    QVBoxLayout as QVBoxLayout2
)

from widgets.adapter_card import AdapterCard
from widgets.traffic_graph import TrafficGraph


class NetworkPage(QWidget):

    def __init__(self):
        super().__init__()

        root = QVBoxLayout(self)

        # Title
        title = QLabel("Network Center")
        title.setObjectName("PageTitle")
        root.addWidget(title)

        # --- Traffic graph ---
        self.traffic = TrafficGraph()
        root.addWidget(self.traffic)

        # --- Stats row ---
        stats = QGridLayout()
        cards = ["Total Download", "Total Upload", "Connections", "Latency"]

        for i, text in enumerate(cards):
            card = QFrame()
            card.setObjectName("card")

            layout = QVBoxLayout2(card)
            layout.addWidget(QLabel(text))
            layout.addWidget(QLabel("0"))

            stats.addWidget(card, 0, i)

        root.addLayout(stats)

        # --- Scroll area with adapters ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        container = QWidget()
        self.layout_cards = QVBoxLayout(container)

        adapters = [
            ("WiFi", "Intel AX210"),
            ("Ethernet", "Realtek PCIe"),
            ("Ethernet 2", "Intel I225"),
            ("VPN", "OpenVPN"),
            ("Bluetooth", "Intel BT"),
            ("VirtualBox", "VBox Driver"),
            ("Hyper-V", "Hyper-V Switch"),
            ("VMware", "VMNet"),
            ("Docker", "Docker Adapter"),
            ("WSL", "WSL Virtual NIC")
        ]

        for name, driver in adapters:
            self.layout_cards.addWidget(AdapterCard(name, driver))

        self.layout_cards.addStretch()
        scroll.setWidget(container)

        root.addWidget(scroll)
