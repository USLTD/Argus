from PyQt5.QtWidgets import (
    QTableWidget,
    QTableWidgetItem
)


class PartitionTable(
    QTableWidget
):

    def __init__(self):
        super().__init__()

        self.setColumnCount(5)

        self.setHorizontalHeaderLabels([
            "Drive",
            "Partition",
            "File System",
            "Size",
            "Free"
        ])

        rows = [
            [
                "C:",
                "System",
                "NTFS",
                "500 GB",
                "210 GB"
            ],
            [
                "D:",
                "Games",
                "NTFS",
                "2 TB",
                "900 GB"
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