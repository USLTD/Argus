from PyQt5.QtWidgets import (
    QTableWidget,
    QTableWidgetItem
)


class ConnectionTable(QTableWidget):

    def __init__(self):
        super().__init__()

        self.setColumnCount(5)

        self.setHorizontalHeaderLabels([
            "Protocol",
            "Local",
            "Remote",
            "Port",
            "State"
        ])

        rows = [
            ["TCP","127.0.0.1","8.8.8.8","443","ESTABLISHED"],
            ["UDP","0.0.0.0","1.1.1.1","53","LISTENING"],
            ["TCP","192.168.1.10","142.250.74.14","443","ESTABLISHED"]
        ]

        self.setRowCount(len(rows))

        for r,row in enumerate(rows):
            for c,val in enumerate(row):
                self.setItem(
                    r,
                    c,
                    QTableWidgetItem(val)
                )