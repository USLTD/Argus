import random

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
    QPushButton,
    QWidget
)

from widgets.graph_widget import GraphWidget


class AdapterCard(QFrame):

    def __init__(self, adapter_name, adapter_type):
        super().__init__()

        self.adapter_name = adapter_name
        self.setObjectName("adapterCard")

        layout = QVBoxLayout(self)

        # Basic info
        self.title = QLabel(f"{adapter_name}")
        self.status = QLabel("Status: Connected")
        self.download = QLabel()
        self.upload = QLabel()
        self.latency = QLabel()
        self.ip = QLabel(f"IP: 192.168.1.{random.randint(1,254)}")
        self.mac = QLabel("MAC: 00-15-5D-AB-CD-EF")
        self.driver = QLabel(f"Driver: {adapter_type}")

        # Expand button + graph
        self.expand_btn = QPushButton("Details")
        self.graph = GraphWidget()
        self.graph.hide()

        # Details widget (created once)
        self.details_widget = QWidget()
        details_layout = QVBoxLayout(self.details_widget)
        details_layout.addWidget(QLabel("DNS: 8.8.8.8"))
        details_layout.addWidget(QLabel("Gateway: 192.168.1.1"))
        details_layout.addWidget(QLabel("Driver Date: 2025"))
        details_layout.addWidget(QLabel("MTU: 1500"))
        self.details_widget.hide()

        # Add widgets to layout
        layout.addWidget(self.title)
        layout.addWidget(self.status)
        layout.addWidget(self.download)
        layout.addWidget(self.upload)
        layout.addWidget(self.latency)
        layout.addWidget(self.ip)
        layout.addWidget(self.mac)
        layout.addWidget(self.driver)
        layout.addWidget(self.expand_btn)
        layout.addWidget(self.graph)
        layout.addWidget(self.details_widget)

        # Button toggles details
        self.expand_btn.clicked.connect(self.toggle_details)

        # Timer updates stats
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(1000)

        self.update_stats()

    def toggle_details(self):
        state = not self.details_widget.isVisible()
        self.details_widget.setVisible(state)
        self.graph.setVisible(state)

    def update_stats(self):
        down = round(random.uniform(0, 100), 2)
        up = round(random.uniform(0, 30), 2)
        ping = random.randint(5, 100)

        self.download.setText(f"Download: {down} Mbps")
        self.upload.setText(f"Upload: {up} Mbps")
        self.latency.setText(f"Latency: {ping} ms")
