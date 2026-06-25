from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QStackedWidget,
    QPushButton
)

from PyQt6.QtGui import QAction


from frontend.ui.sidebar import Sidebar
from frontend.ui.top_toolbar import TopToolbar
from frontend.ui.status_bar import StatusBar


from frontend.pages.overview_page import OverviewPage
from frontend.pages.cpu_page import CPUPage
from frontend.pages.memory_page import MemoryPage
from frontend.pages.disk_page import DiskPage
from frontend.pages.network_page import NetworkPage
from frontend.pages.processes_page import ProcessesPage
from frontend.pages.recording_page import RecordingPage
from frontend.pages.system_page import SystemPage
from frontend.pages.settings_page import SettingsPage
from frontend.pages.about_page import AboutPage



class MainWindow(QMainWindow):


    def __init__(self, bridge):

        super().__init__()

        self._bridge = bridge


        self.setWindowTitle(
            "ARGUS - Observe Everything"
        )


        self.resize(
            1800,
            1000
        )



        # Toolbar

        self.toolbar = TopToolbar()

        self.addToolBar(
            self.toolbar
        )



        # Status bar

        self.setStatusBar(
            StatusBar()
        )



        # Central widget

        central = QWidget()

        self.setCentralWidget(
            central
        )



        main_layout = QHBoxLayout(
            central
        )



        # ==========================
        # SIDEBAR
        # ==========================


        self.sidebar = Sidebar()



        sidebar_container = QWidget()



        sidebar_layout = QVBoxLayout(
            sidebar_container
        )


        sidebar_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )



        self.toggle_button = QPushButton(
            "☰"
        )


        self.toggle_button.setFixedHeight(
            40
        )


        self.toggle_button.clicked.connect(
            self.sidebar.toggle_sidebar
        )






        sidebar_layout.addWidget(
            self.toggle_button
        )


        sidebar_layout.addWidget(
            self.sidebar
        )



        # ==========================
        # PAGES
        # ==========================


        self.stack = QStackedWidget()



        main_layout.addWidget(
            sidebar_container
        )


        main_layout.addWidget(
            self.stack,
            1
        )



        self.build_pages(self._bridge)



        self.sidebar.currentRowChanged.connect(
            self.stack.setCurrentIndex
        )



        self.sidebar.setCurrentRow(
            0
        )



        refresh_action = QAction(
            self
        )


        refresh_action.setShortcut(
            "F5"
        )


        self.addAction(
            refresh_action
        )



    def build_pages(self, bridge):


        self.stack.addWidget(
            OverviewPage(bridge=bridge)
        )


        self.stack.addWidget(
            ProcessesPage(bridge=bridge)
        )


        self.stack.addWidget(
            SystemPage(bridge=bridge)
        )


        self.stack.addWidget(
            CPUPage(bridge=bridge)
        )


        self.stack.addWidget(
            MemoryPage(bridge=bridge)
        )


        self.stack.addWidget(
            DiskPage(bridge=bridge)
        )


        self.stack.addWidget(
            NetworkPage(bridge=bridge)
        )


        self.stack.addWidget(
            RecordingPage(bridge=bridge)
        )


        self.stack.addWidget(
            SettingsPage(bridge=bridge)
        )


        self.stack.addWidget(
            AboutPage(bridge=bridge)
        )