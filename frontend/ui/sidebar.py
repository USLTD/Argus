from PyQt6.QtWidgets import QListWidget, QListWidgetItem
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSize


class Sidebar(QListWidget):
    PAGES = [
        ("Overview", "frontend/assets/icons/Overview.png"),
        ("Processes", "frontend/assets/icons/Processes.png"),
        ("System", "frontend/assets/icons/System.png"),
        ("Performance", "frontend/assets/icons/Performance.png"),
        ("Memory", "frontend/assets/icons/Memory.png"),
        ("Disk", "frontend/assets/icons/Disk.png"),
        ("Network", "frontend/assets/icons/Network.png"),
        ("Time Machine", "frontend/assets/icons/TimeMachine.png"),
        ("Settings", "frontend/assets/icons/Settings.png"),
        ("Information", "frontend/assets/icons/Information.png"),
    ]

    def __init__(self):

        super().__init__()

        self.expanded = True

        self.setMaximumWidth(220)
        self.setIconSize(QSize(28, 28))

        self._page_items: list[QListWidgetItem] = []

        for name, icon_path in self.PAGES:
            item = QListWidgetItem()

            item.setText(name)

            item.setIcon(QIcon(icon_path))

            item.setToolTip(name)

            self.addItem(item)

            self._page_items.append(item)

    def toggle_sidebar(self):

        if self.expanded:
            self.collapse()

        else:
            self.expand()

    def collapse(self):

        self.setMaximumWidth(70)

        for item in self._page_items:
            item.setText("")

        self.expanded = False

    def expand(self):

        self.setMaximumWidth(220)

        for item, page in zip(self._page_items, self.PAGES):
            item.setText(page[0])

        self.expanded = True
