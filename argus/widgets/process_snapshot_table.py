from PyQt5.QtWidgets import (
    QTableWidget,
    QTableWidgetItem
)


class ProcessSnapshotTable(
    QTableWidget
):

    def __init__(self):
        super().__init__()

        self.setColumnCount(5)

        self.setHorizontalHeaderLabels([
            "PID",
            "Process",
            "CPU",
            "RAM",
            "State"
        ])

        rows = [

            [
                "1500",
                "chrome.exe",
                "8%",
                "1200 MB",
                "Running"
            ],

            [
                "1044",
                "explorer.exe",
                "1%",
                "180 MB",
                "Running"
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