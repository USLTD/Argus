from PyQt6.QtWidgets import QToolBar, QLineEdit, QLabel, QPushButton, QApplication

from PyQt6.QtCore import QTimer
from datetime import datetime

from frontend.core.theme_manager import ThemeManager


class TopToolbar(QToolBar):
    def __init__(self, user=None):

        super().__init__()

        self.user = user

        self.current_theme = "light"

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search...")

        self.refresh_btn = QPushButton("Refresh")
        self.export_btn = QPushButton("Export")
        self.theme_btn = QPushButton("🌙 Dark Mode")

        self.theme_btn.clicked.connect(self.toggle_theme)

        self.time_label = QLabel()

        if user:
            self.user_label = QLabel(f"{user.username} ({user.role})")
        else:
            self.user_label = QLabel("Guest")

        self.addWidget(self.search)
        self.addWidget(self.refresh_btn)
        self.addWidget(self.export_btn)
        self.addWidget(self.theme_btn)

        self.addSeparator()

        self.addWidget(self.user_label)

        self.addSeparator()

        self.addWidget(self.time_label)

        timer = QTimer(self)
        timer.timeout.connect(self.update_time)
        timer.start(1000)

        self.update_time()

    def toggle_theme(self):

        app = QApplication.instance()

        if self.current_theme == "light":
            ThemeManager.apply_theme(app, "dark")

            self.current_theme = "dark"
            self.theme_btn.setText("☀ Light Mode")

        else:
            ThemeManager.apply_theme(app, "light")

            self.current_theme = "light"
            self.theme_btn.setText("🌙 Dark Mode")

    def update_time(self):

        self.time_label.setText(datetime.now().strftime("%H:%M:%S"))
