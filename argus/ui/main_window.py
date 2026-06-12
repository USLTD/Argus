from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QStackedWidget,
    QDockWidget
)

from pages.overview import OverviewPage
from pages.processes import ProcessesPage
from pages.system import SystemPage
from pages.network import NetworkPage
from pages.memory import MemoryPage
from pages.disk import DiskPage
from pages.drivers import DriversPage
from pages.scripts import ScriptsPage
from pages.rules import RulesPage
from pages.timemachine import TimeMachinePage
from pages.recording import RecordingPage
from pages.users import UsersPage
from pages.settings import SettingsPage
from pages.about import AboutPage

from ui.sidebar import Sidebar
from ui.topbar import TopBar
from widgets.notification_center import NotificationCenter


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Argus")
        self.resize(1600, 900)

        central = QWidget()
        self.setCentralWidget(central)

        root = QHBoxLayout(central)

        self.sidebar = Sidebar()
        root.addWidget(self.sidebar)

        right = QVBoxLayout()
        root.addLayout(right)

        self.topbar = TopBar()
        right.addWidget(self.topbar)

        self.stack = QStackedWidget()
        right.addWidget(self.stack)

        self.pages = {
            "overview": OverviewPage(),
            "processes": ProcessesPage(),
            "system": SystemPage(),
            "network": NetworkPage(),
            "memory": MemoryPage(),
            "disk": DiskPage(),
            "drivers": DriversPage(),
            "scripts": ScriptsPage(),
            "rules": RulesPage(),
            "timemachine": TimeMachinePage(),
            "recording": RecordingPage(),
            "users": UsersPage(),
            "settings": SettingsPage(),
            "about": AboutPage()
        }

        # Add pages to stacked widget
        for page in self.pages.values():
            self.stack.addWidget(page)

        # Default page
        self.stack.setCurrentWidget(self.pages["overview"])

        # Connect sidebar buttons
        for page_name, button in self.sidebar.buttons.items():
            button.clicked.connect(
                lambda checked=False, name=page_name: self.show_page(name)
            )

        # Notification Center
        self.notifications = NotificationCenter()

        dock = QDockWidget("Notifications", self)
        dock.setWidget(self.notifications)
        dock.setAllowedAreas(Qt.RightDockWidgetArea)

        self.addDockWidget(Qt.RightDockWidgetArea, dock)
        dock.hide()

    def show_page(self, page_name):
        if page_name in self.pages:
            self.stack.setCurrentWidget(self.pages[page_name])