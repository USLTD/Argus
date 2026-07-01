from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit


class SearchPanel(QWidget):
    def __init__(self):

        super().__init__()

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Global Search"))

        self.search = QLineEdit()

        layout.addWidget(self.search)
