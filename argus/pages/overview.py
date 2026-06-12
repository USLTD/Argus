from PyQt5.QtWidgets import (
    QWidget,
    QGridLayout
)

from widgets.stat_card import StatCard


class OverviewPage(QWidget):

    def __init__(self):
        super().__init__()

        layout = QGridLayout(self)

        cards = [
            "CPU",
            "RAM",
            "Disk",
            "GPU",
            "Network",
            "Temperature",
            "Power",
            "System Load"
        ]

        row = 0
        col = 0

        for card in cards:

            layout.addWidget(
                StatCard(card),
                row,
                col
            )

            col += 1

            if col == 2:
                col = 0
                row += 1