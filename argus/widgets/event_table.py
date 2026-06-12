from PyQt5.QtWidgets import (
    QTableWidget,
    QTableWidgetItem
)


class EventTable(QTableWidget):

    def __init__(self):
        super().__init__()

        self.setColumnCount(4)

        self.setHorizontalHeaderLabels([
            "Time",
            "Category",
            "Event",
            "Severity"
        ])

        rows = [

            [
                "09:10:22",
                "Process",
                "chrome.exe started",
                "Info"
            ],

            [
                "09:12:01",
                "Memory",
                "RAM Spike",
                "Warning"
            ],

            [
                "09:15:18",
                "Network",
                "Connection Burst",
                "Critical"
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