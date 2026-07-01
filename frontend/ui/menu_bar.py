from PyQt6.QtWidgets import QMenuBar


class ArgusMenuBar(QMenuBar):
    def __init__(self):

        super().__init__()

        file_menu = self.addMenu("&File")

        file_menu.addAction("Export")
        file_menu.addAction("Screenshot")
        file_menu.addSeparator()
        file_menu.addAction("Exit")

        view_menu = self.addMenu("&View")

        view_menu.addAction("Light Theme")
        view_menu.addAction("Dark Theme")
        view_menu.addAction("System Theme")

        tools_menu = self.addMenu("&Tools")

        tools_menu.addAction("Process Manager")
        tools_menu.addAction("Recording Manager")

        help_menu = self.addMenu("&Help")

        help_menu.addAction("About")
