from PyQt5.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem
)


class UsersPage(QWidget):

    def __init__(self):

        super().__init__()

        root = QVBoxLayout(self)

        title = QLabel(
            "Users & Permissions"
        )

        title.setObjectName(
            "PageTitle"
        )

        root.addWidget(title)

        table = QTableWidget()

        table.setColumnCount(6)

        table.setHorizontalHeaderLabels([
            "User",
            "Role",
            "Drivers",
            "Scripts",
            "Rules",
            "Time Machine"
        ])

        rows = [

            [
                "Administrator",
                "Admin",
                "Yes",
                "Yes",
                "Yes",
                "Yes"
            ],

            [
                "Standard User",
                "User",
                "No",
                "No",
                "No",
                "No"
            ]
        ]

        table.setRowCount(
            len(rows)
        )

        for r,row in enumerate(rows):

            for c,val in enumerate(row):

                table.setItem(
                    r,
                    c,
                    QTableWidgetItem(val)
                )

        root.addWidget(
            table
        )