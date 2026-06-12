from PyQt5.QtWidgets import (
    QListWidget
)


class NotificationCenter(
    QListWidget
):

    def __init__(self):
        super().__init__()

        self.addItem(
            "System Ready"
        )

        self.addItem(
            "Network Connected"
        )

        self.addItem(
            "Mock Alert Generated"
        )