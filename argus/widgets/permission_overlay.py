from PyQt5.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout
)

from core.role_manager import (
    RoleManager
)


class PermissionOverlay(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        label = QLabel(
            "Administrator Access Required"
        )

        layout.addWidget(
            label
        )

        self.hide()

    def refresh(self):

        self.setVisible(
            not RoleManager.is_admin()
        )