import sys

from PyQt6.QtWidgets import QApplication

from frontend.core.app import ArgusApplication


def main():
    app = QApplication(sys.argv)

    argus = ArgusApplication(app)

    argus.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()