import random

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QTreeWidget,
    QTreeWidgetItem
)


class ProcessTree(QTreeWidget):

    def __init__(self):
        super().__init__()

        self.setColumnCount(11)

        self.setHeaderLabels([
            "PID",
            "Name",
            "CPU %",
            "RAM MB",
            "GPU %",
            "Disk",
            "Network",
            "Threads",
            "User",
            "Status",
            "Parent PID"
        ])

        self.setAlternatingRowColors(True)

        self.populate()

    def populate(self):

        chrome = QTreeWidgetItem([
            "1524",
            "chrome.exe",
            "8.4",
            "1280",
            "5",
            "2 MB/s",
            "1 MB/s",
            "34",
            "Admin",
            "Running",
            "0"
        ])

        self.addTopLevelItem(chrome)

        for i in range(3):

            child = QTreeWidgetItem([
                str(2000+i),
                "renderer.exe",
                str(random.randint(1,10)),
                str(random.randint(100,500)),
                str(random.randint(0,5)),
                "0.5 MB/s",
                "0.3 MB/s",
                str(random.randint(5,20)),
                "Admin",
                "Running",
                "1524"
            ])

            chrome.addChild(child)

        gpu = QTreeWidgetItem([
            "2100",
            "gpu.exe",
            "2",
            "200",
            "12",
            "0.1 MB/s",
            "0.0 MB/s",
            "5",
            "Admin",
            "Running",
            "1524"
        ])

        chrome.addChild(gpu)

        explorer = QTreeWidgetItem([
            "1044",
            "explorer.exe",
            "1",
            "180",
            "0",
            "0.0",
            "0.0",
            "10",
            "User",
            "Running",
            "0"
        ])

        self.addTopLevelItem(explorer)

        system = QTreeWidgetItem([
            "4",
            "System",
            "0.2",
            "50",
            "0",
            "0",
            "0",
            "120",
            "SYSTEM",
            "Running",
            "0"
        ])

        self.addTopLevelItem(system)

        chrome.setExpanded(True)