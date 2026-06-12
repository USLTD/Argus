from PyQt5.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QPushButton,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem
)
from widgets.permission_overlay import PermissionOverlay


class RulesPage(QWidget):

    def __init__(self):

        super().__init__()

        root = QVBoxLayout(self)

        title = QLabel(
            "Rule Engine"
        )

        title.setObjectName(
            "PageTitle"
        )

        root.addWidget(title)

        buttons = QHBoxLayout()

        buttons.addWidget(
            QPushButton("Add")
        )

        buttons.addWidget(
            QPushButton("Edit")
        )

        buttons.addWidget(
            QPushButton("Delete")
        )

        root.addLayout(
            buttons
        )

        table = QTableWidget()

        table.setColumnCount(5)

        table.setHorizontalHeaderLabels([
            "Rule",
            "Condition",
            "Action",
            "Enabled",
            "Priority"
        ])

        rules = [

            [
                "High CPU",
                "> 90%",
                "Notify",
                "Yes",
                "High"
            ],

            [
                "Disk Full",
                ">95%",
                "Alert",
                "Yes",
                "Critical"
            ]
        ]

        table.setRowCount(
            len(rules)
        )

        for r,row in enumerate(
                rules
        ):

            for c,val in enumerate(
                    row
            ):

                table.setItem(
                    r,
                    c,
                    QTableWidgetItem(val)
                )

        root.addWidget(
            table
        )

        self.overlay = PermissionOverlay()
        root.addWidget(self.overlay)

    def refresh_permissions(self):
        self.overlay.refresh()
