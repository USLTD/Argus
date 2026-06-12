from PyQt5.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit
)

from widgets.driver_table import (
    DriverTable
)
from widgets.permission_overlay import PermissionOverlay


class DriversPage(QWidget):

    def __init__(self):

        super().__init__()

        root = QVBoxLayout(self)

        title = QLabel(
            "Driver Manager"
        )

        title.setObjectName(
            "PageTitle"
        )

        root.addWidget(title)

        toolbar = QHBoxLayout()

        self.search = QLineEdit()

        self.search.setPlaceholderText(
            "Search drivers..."
        )

        toolbar.addWidget(
            self.search
        )

        self.install = QPushButton(
            "Install"
        )

        self.remove = QPushButton(
            "Remove"
        )

        self.update = QPushButton(
            "Update"
        )

        toolbar.addWidget(
            self.install
        )

        toolbar.addWidget(
            self.remove
        )

        toolbar.addWidget(
            self.update
        )

        root.addLayout(toolbar)

        self.table = DriverTable()

        root.addWidget(
            self.table
        )
        self.overlay = PermissionOverlay()
        root.addWidget(self.overlay)

    def refresh_permissions(self):
        self.overlay.refresh()
