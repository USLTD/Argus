from PyQt5.QtWidgets import (
    QTableWidget,
    QTableWidgetItem
)


class ServicesTable(QTableWidget):

    def __init__(self):
        super().__init__()

        self.setColumnCount(3)

        self.setHorizontalHeaderLabels([
            "Service",
            "Status",
            "Startup"
        ])

        services = [
            [
                "Windows Update",
                "Running",
                "Auto"
            ],
            [
                "Argus Mock Agent",
                "Running",
                "Auto"
            ],
            [
                "Docker",
                "Stopped",
                "Manual"
            ]
        ]

        self.setRowCount(
            len(services)
        )

        for r, row in enumerate(
                services
        ):
            for c, value in enumerate(
                    row
            ):
                self.setItem(
                    r,
                    c,
                    QTableWidgetItem(value)
                )