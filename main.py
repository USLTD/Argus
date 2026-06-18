import sys
from PyQt5.QtWidgets import QApplication
from frontend.ui.main_window import MainWindow
from frontend.ui.splash import ArgusSplash

def main():
    app = QApplication(sys.argv)

    # Apply theme
    with open("frontend/themes/dark.qss", "r", encoding="utf8") as f:
        app.setStyleSheet(f.read())

    # Show splash screen
    splash = ArgusSplash()
    splash.show()

    # Main window
    window = MainWindow()
    window.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
