from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTabWidget,
    QComboBox,
    QCheckBox,
    QLabel
)


class SettingsPage(QWidget):

    def __init__(self, bridge=None):

        super().__init__()

        layout = QVBoxLayout(self)

        tabs = QTabWidget()

        tabs.addTab(
            self.general_tab(),
            "General"
        )

        tabs.addTab(
            self.appearance_tab(),
            "Appearance"
        )

        tabs.addTab(
            self.notifications_tab(),
            "Notifications"
        )

        tabs.addTab(
            self.recording_tab(),
            "Recording"
        )

        layout.addWidget(tabs)

    def general_tab(self):

        widget = QWidget()

        layout = QVBoxLayout(widget)

        layout.addWidget(
            QCheckBox(
                "Start with Windows"
            )
        )

        layout.addWidget(
            QCheckBox(
                "Minimize to Tray"
            )
        )

        return widget

    def appearance_tab(self):

        widget = QWidget()

        layout = QVBoxLayout(widget)

        combo = QComboBox()

        combo.addItems([
            "Light",
            "Dark",
            "System"
        ])

        layout.addWidget(
            QLabel("Theme")
        )

        layout.addWidget(combo)

        return widget

    def notifications_tab(self):

        widget = QWidget()

        layout = QVBoxLayout(widget)

        layout.addWidget(
            QCheckBox(
                "Enable Alerts"
            )
        )

        return widget

    def recording_tab(self):

        widget = QWidget()

        layout = QVBoxLayout(widget)

        layout.addWidget(
            QLabel(
                "Recording Settings"
            )
        )

        return widget