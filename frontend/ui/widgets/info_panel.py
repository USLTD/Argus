from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout

class SystemSummary(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("System Summary Placeholder"))
        self.setLayout(layout)
