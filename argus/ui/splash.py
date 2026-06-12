from PyQt5.QtWidgets import QSplashScreen
from PyQt5.QtGui import QPixmap


class ArgusSplash(QSplashScreen):
    def __init__(self):
        # Create a blank pixmap (600x300) or load an image
        super().__init__(QPixmap(600, 300))

        # Show startup message
        self.showMessage(
            "Starting Argus...",
            alignment=0  # default alignment (can use Qt.AlignCenter)
        )
