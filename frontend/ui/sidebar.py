from PyQt6.QtWidgets import QListWidget, QListWidgetItem
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSize


class Sidebar(QListWidget):

    PAGES = [
        ("Overview", "assets/icons/Overview.png"),
        ("Processes", "assets/icons/Processes.png"),
        ("System", "assets/icons/System.png"),
        ("Performance", "assets/icons/Performance.png"),
        ("Memory", "assets/icons/Memory.png"),
        ("Disk", "assets/icons/Disk.png"),
        ("Network", "assets/icons/Network.png"),
        ("Time Machine", "assets/icons/TimeMachine.png"),
        ("Settings", "assets/icons/Settings.png"),
        ("Information", "assets/icons/Information.png"),
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