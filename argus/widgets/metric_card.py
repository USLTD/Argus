from PyQt5.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout
)


class MetricCard(QFrame):

    def __init__(
            self,
            title,
            value="0",
            unit=""
    ):
        super().__init__()

        self.setObjectName("card")

        layout = QVBoxLayout(self)

        self.title = QLabel(title)

        self.value = QLabel(
            f"{value} {unit}"
        )

        self.value.setObjectName(
            "MetricValue"
        )

        layout.addWidget(self.title)
        layout.addWidget(self.value)

    def set_value(
            self,
            value,
            unit=""
    ):
        self.value.setText(
            f"{value} {unit}"
        )