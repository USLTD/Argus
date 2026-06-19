from PyQt6.QtWidgets import (
    QTableWidget,
    QTableWidgetItem
)


class AdapterTable(
    QTableWidget
):

    def __init__(self):

        super().__init__()

        self.setColumnCount(9)

        self.setHorizontalHeaderLabels(
            [
                "Name",
                "Status",
                "IP",
                "MAC",
                "Download",
                "Upload",
                "Latency",
                "Gateway",
                "DNS"
            ]
        )

        adapters = [
            "Ethernet",
            "WiFi",
            "VPN",
            "Docker",
            "VMWare",
            "Hyper-V",
            "Loopback"
        ]

        self.setRowCount(
            len(adapters)
        )

        for row, name in enumerate(
            adapters
        ):
            self.setItem(
                row,
                0,
                QTableWidgetItem(name)
            )