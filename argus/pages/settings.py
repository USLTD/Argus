from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QTabWidget,
    QComboBox,
    QFormLayout
)


class SettingsPage(QWidget):

    def __init__(self):

        super().__init__()

        root = QVBoxLayout(self)

        title = QLabel(
            "Settings"
        )

        title.setObjectName(
            "PageTitle"
        )

        root.addWidget(title)

        tabs = QTabWidget()

        general = QWidget()
        appearance = QWidget()
        notifications = QWidget()
        advanced = QWidget()

        tabs.addTab(
            general,
            "General"
        )

        tabs.addTab(
            appearance,
            "Appearance"
        )

        tabs.addTab(
            notifications,
            "Notifications"
        )

        tabs.addTab(
            advanced,
            "Advanced"
        )

        appearance_layout = (
            QFormLayout(
                appearance
            )
        )

        theme = QComboBox()

        theme.addItems([
            "Dark",
            "Light",
            "System"
        ])

        appearance_layout.addRow(
            "Theme",
            theme
        )

        root.addWidget(
            tabs
        )