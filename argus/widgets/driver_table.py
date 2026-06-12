from PyQt5.QtWidgets import (
    QTableWidget,
    QTableWidgetItem
)


class DriverTable(
    QTableWidget
):

    def __init__(self):
        super().__init__()

        self.setColumnCount(5)

        self.setHorizontalHeaderLabels([
            "Driver",
            "Provider",
            "Version",
            "Date",
            "Status"
        ])

        rows = [

            [
                "NVIDIA Driver",
                "NVIDIA",
                "572.11",
                "2026",
                "Loaded"
            ],

            [
                "Intel WiFi",
                "Intel",
                "24.0",
                "2025",
                "Loaded"
            ],

            [
                "VirtualBox",
                "Oracle",
                "8.0",
                "2026",
                "Loaded"
            ]
        ]

        self.setRowCount(
            len(rows)
        )

        for r,row in enumerate(rows):

            for c,val in enumerate(row):

                self.setItem(
                    r,
                    c,
                    QTableWidgetItem(val)
                )