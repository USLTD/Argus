from PyQt6.QtWidgets import QDockWidget, QTextEdit


class EventLogDock(QDockWidget):
    def __init__(self):

        super().__init__("Event Log")

        self.log = QTextEdit()

        self.log.setReadOnly(True)

        self.setWidget(self.log)

    def add_entry(self, text):
        self.log.append(text)
