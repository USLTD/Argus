from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QComboBox


class ProcessFilter(QWidget):
    def __init__(self):

        super().__init__()

        layout = QHBoxLayout(self)

        self.search = QLineEdit()

        self.search.setPlaceholderText("Filter...")

        self.group = QComboBox()

        self.group.addItems(["All", "Running", "Suspended", "System"])

        layout.addWidget(self.search)

        layout.addWidget(self.group)
