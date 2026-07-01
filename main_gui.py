import sys

from PyQt6.QtWidgets import QApplication

from backend.core.engine import BackendEngine
from frontend.core.app import ArgusApplication


def main():
    app = QApplication(sys.argv)

    engine = BackendEngine()
    argus = ArgusApplication(app, engine=engine)

    argus.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
