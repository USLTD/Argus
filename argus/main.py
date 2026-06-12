import sys
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow
from ui.splash import ArgusSplash   # ✅ import splash

def main():
    app = QApplication(sys.argv)

    # Apply theme
    with open("themes/dark.qss", "r", encoding="utf8") as f:
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
