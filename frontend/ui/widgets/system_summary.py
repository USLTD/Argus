from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel
)


class SystemSummary(QWidget):

    def __init__(self):

        super().__init__()

        layout = QVBoxLayout(self)

        layout.addWidget(
            QLabel(
                "CPU Usage"
            )
        )

        layout.addWidget(
            QLabel(
                "Memory Usage"
            )
        )

        layout.addWidget(
            QLabel(
                "Disk Activity"
            )
        )

        layout.addWidget(
            QLabel(
                "Network Activity"
            )
        )