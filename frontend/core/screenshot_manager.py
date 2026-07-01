from PyQt6.QtWidgets import QFileDialog


class ScreenshotManager:
    @staticmethod
    def save_widget(widget):

        path, _ = QFileDialog.getSaveFileName(None, "Save Screenshot", "", "*.png")

        if not path:
            return

        widget.grab().save(path)
