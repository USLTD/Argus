from PyQt5.QtCore import Qt, QPropertyAnimation
from PyQt5.QtWidgets import QWidget, QPushButton, QVBoxLayout
from resources.icon_manager import IconManager


class Sidebar(QWidget):

    def __init__(self):
        super().__init__()

        self.expanded = True
        self.setMinimumWidth(220)

        layout = QVBoxLayout(self)
        self.buttons = {}

        items = [
            ("overview", "Overview"),
            ("processes", "Processes"),
            ("system", "System"),
            ("network", "Network"),
            ("memory", "Memory"),
            ("disk", "Disk"),
            ("recording", "Recording"),
            ("users", "Users"),
            ("settings", "Settings"),
            ("about", "About")
        ]
        self.collapse_btn = QPushButton("☰")
        layout.addWidget(self.collapse_btn)

        for key, text in items:
            btn = QPushButton(text)
            btn.setIcon(IconManager.get(key))
            btn.setCursor(Qt.PointingHandCursor)
            self.buttons[key] = btn
            layout.addWidget(btn)

        layout.addStretch()

        self.animation = QPropertyAnimation(self, b"minimumWidth")
        self.animation.setDuration(250)

        self.collapse_btn.clicked.connect(self.toggle)

    def toggle(self):
        if self.expanded:
            self.animation.setStartValue(220)
            self.animation.setEndValue(70)

            for btn in self.buttons.values():
                btn.setText("")

        else:
            self.animation.setStartValue(70)
            self.animation.setEndValue(220)

            labels = {
                "overview": "Overview",
                "processes": "Processes",
                "system": "System",
                "network": "Network",
                "memory": "Memory",
                "disk": "Disk",
                "drivers": "Drivers",
                "scripts": "Scripts",
                "rules": "Rules",
                "timemachine": "Time Machine",
                "recording": "Recording",
                "users": "Users",
                "settings": "Settings",
                "about": "About"
            }

            for key, btn in self.buttons.items():
                btn.setText(labels[key])

        self.animation.start()
        self.expanded = not self.expanded