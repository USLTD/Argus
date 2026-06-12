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


class ScriptsPage(QWidget):

    def __init__(self):

        super().__init__()

        root = QVBoxLayout(self)

        title = QLabel(
            "Script Manager"
        )

        title.setObjectName(
            "PageTitle"
        )

        root.addWidget(title)

        buttons = QHBoxLayout()

        names = [
            "New",
            "Edit",
            "Delete",
            "Run",
            "Stop",
            "Import",
            "Export"
        ]

        for name in names:

            buttons.addWidget(
                QPushButton(name)
            )

        root.addLayout(
            buttons
        )

        self.table = QTableWidget()

        self.table.setColumnCount(5)

        self.table.setHorizontalHeaderLabels([
            "Name",
            "Language",
            "Status",
            "Last Run",
            "Schedule"
        ])

        scripts = [
            [
                "Cleanup",
                "Python",
                "Idle",
                "Yesterday",
                "Daily"
            ],
            [
                "Backup",
                "PowerShell",
                "Running",
                "Now",
                "Hourly"
            ]
        ]

        self.table.setRowCount(
            len(scripts)
        )

        for r,row in enumerate(
                scripts
        ):

            for c,val in enumerate(
                    row
            ):

                self.table.setItem(
                    r,
                    c,
                    QTableWidgetItem(val)
                )

        root.addWidget(
            self.table
        )

        self.overlay = PermissionOverlay()
        root.addWidget(self.overlay)

    def refresh_permissions(self):
        self.overlay.refresh()
