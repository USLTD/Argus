from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel
)

import sys

from PyQt6.QtCore import QT_VERSION_STR


class AboutPage(QWidget):

    def __init__(self, bridge=None):

        super().__init__()

        layout = QVBoxLayout(self)

        layout.addWidget(
            QLabel("ARGUS")
        )

        layout.addWidget(
            QLabel(
                "Observe Everything"
            )
        )

        layout.addWidget(
            QLabel(
                "Version 1.0"
            )
        )

        layout.addWidget(
            QLabel(
                f"Qt {QT_VERSION_STR}"
            )
        )

        layout.addWidget(
            QLabel(
                f"Python {sys.version}"
            )
        )

        layout.addWidget(
            QLabel(
                "GitHub: Placeholder"
            )
        )