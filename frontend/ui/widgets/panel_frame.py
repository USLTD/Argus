from PyQt6.QtWidgets import QFrame
from PyQt6.QtWidgets import QVBoxLayout
from PyQt6.QtWidgets import QLabel


class PanelFrame(QFrame):
    def __init__(self, title):

        super().__init__()

        layout = QVBoxLayout(self)

        label = QLabel(title)

        layout.addWidget(label)
