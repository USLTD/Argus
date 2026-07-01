from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
)

from PyQt6.QtCore import QT_VERSION_STR
import platform
import sys

from frontend.core.engine_bridge import EngineBridge


class AboutPage(QWidget):
    def __init__(self, bridge: EngineBridge | None = None):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        title = QLabel("<h1>ARGUS</h1>")
        layout.addWidget(title)

        layout.addWidget(QLabel("<b>Observe Everything</b>"))

        layout.addWidget(QLabel("Cross-platform system monitor and process manager."))

        layout.addWidget(QLabel(""))

        layout.addWidget(QLabel("<b>Application</b>"))
        layout.addWidget(QLabel("Version: 1.0"))
        layout.addWidget(QLabel("License: MIT"))

        layout.addWidget(QLabel(""))

        layout.addWidget(QLabel("<b>Features</b>"))
        layout.addWidget(QLabel("• Real-time CPU, Memory, Disk and Network monitoring"))
        layout.addWidget(QLabel("• Process management"))
        layout.addWidget(QLabel("• PyQt6 GUI and Textual TUI"))
        layout.addWidget(QLabel("• Plugin driver architecture"))
        layout.addWidget(QLabel("• Python & Lua scripting support"))
        layout.addWidget(QLabel("• Cross-platform (Windows & Linux)"))

        layout.addWidget(QLabel(""))

        layout.addWidget(QLabel("<b>Runtime</b>"))
        layout.addWidget(QLabel(f"Python: {platform.python_version()}"))
        layout.addWidget(QLabel(f"Qt: {QT_VERSION_STR}"))
        layout.addWidget(QLabel(f"Platform: {platform.system()}"))

        layout.addWidget(QLabel(""))

        layout.addWidget(QLabel("<b>Development Team</b>"))
        layout.addWidget(QLabel("Backend: Luka Mamukashvili"))
        layout.addWidget(QLabel("Frontend: Saba Miqelashvili"))

        layout.addWidget(QLabel(""))

        layout.addWidget(QLabel("<b>Architecture</b>"))
        layout.addWidget(
            QLabel("Driver-based backend • EngineBridge • PyQt6 GUI • Textual TUI")
        )

        layout.addWidget(QLabel(""))

        layout.addWidget(QLabel("<b>GitHub</b>"))
        layout.addWidget(QLabel("https://github.com/<your-repository>"))

        layout.addStretch()
