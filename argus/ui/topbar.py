from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QComboBox
)
from core.role_manager import RoleManager
from datetime import datetime
from widgets.permission_overlay import PermissionOverlay


class TopBar(QWidget):

    def __init__(self):
        super().__init__()

        self.setFixedHeight(60)

        root = QHBoxLayout(self)

        # --- Search bar ---
        self.search = QLineEdit()
        self.search.setPlaceholderText("Global Search...")

        # --- Role selector ---
        self.role = QComboBox()
        self.role.addItems(["Administrator", "Standard User"])
        self.role.currentTextChanged.connect(RoleManager.set_role)

        # --- Theme selector ---
        self.theme = QComboBox()
        self.theme.addItems(["Dark", "Light", "System"])

        # --- Clock ---
        self.clock = QLabel()

        # Add widgets to layout
        root.addWidget(self.search)
        root.addWidget(self.role)
        root.addWidget(self.theme)
        root.addWidget(self.clock)

        # --- Permission overlay ---
        self.overlay = PermissionOverlay()
        root.addWidget(self.overlay)

        # --- Clock timer ---
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)
        self.update_time()

    def update_time(self):
        self.clock.setText(datetime.now().strftime("%H:%M:%S"))

    def refresh_permissions(self):
        self.overlay.refresh()
