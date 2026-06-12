import sys

from PyQt5.QtCore import QT_VERSION_STR

from PyQt5.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout
)


class AboutPage(QWidget):

    def __init__(self):

        super().__init__()

        layout = QVBoxLayout(self)

        title = QLabel(
            "ARGUS"
        )

        title.setObjectName(
            "PageTitle"
        )

        layout.addWidget(title)

        layout.addWidget(
            QLabel(
                "Version: 1.0"
            )
        )

        layout.addWidget(
            QLabel(
                f"Python: {sys.version.split()[0]}"
            )
        )

        layout.addWidget(
            QLabel(
                f"Qt: {QT_VERSION_STR}"
            )
        )

        layout.addWidget(
            QLabel(
                "License: Commercial Demo"
            )
        )

        layout.addWidget(
            QLabel(
                "GitHub: Placeholder"
            )
        )

        layout.addStretch()