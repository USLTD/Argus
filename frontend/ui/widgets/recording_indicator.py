from PyQt6.QtWidgets import QLabel


class RecordingIndicator(
    QLabel
):

    def __init__(self):

        super().__init__()

        self.setText(
            "● REC OFF"
        )

    def start(self):

        self.setText(
            "● REC ON"
        )

    def stop(self):

        self.setText(
            "● REC OFF"
        )