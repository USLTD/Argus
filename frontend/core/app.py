from frontend.ui.main_window import MainWindow


class ArgusApplication:

    def __init__(self, app):
        self.app = app
        self.window = MainWindow()

    def start(self):
        self.window.show()