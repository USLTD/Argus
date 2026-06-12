from PyQt5.QtGui import QPainter, QColor
from PyQt5.QtWidgets import QSlider, QWidget, QVBoxLayout

class TimelineWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.slider = QSlider()
        self.slider.setOrientation(Qt.Horizontal)
        layout.addWidget(self.slider)

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setBrush(QColor(255, 200, 0))

        # Example markers (seconds in a day)
        markers = [100, 500, 900]

        for marker in markers:
            x = marker / 86400 * self.width()
            painter.drawEllipse(int(x), 40, 8, 8)


from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QTabWidget
from widgets.timeline_widget import TimelineWidget
from widgets.playback_controls import PlaybackControls
from widgets.event_table import EventTable
from widgets.process_snapshot_table import ProcessSnapshotTable
from widgets.history_dashboard import HistoryDashboard
from widgets.permission_overlay import PermissionOverlay


class TimeMachinePage(QWidget):

    def __init__(self):
        super().__init__()

        root = QVBoxLayout(self)

        title = QLabel("Time Machine")
        title.setObjectName("PageTitle")
        root.addWidget(title)

        # Permission overlay
        self.overlay = PermissionOverlay()
        root.addWidget(self.overlay)

        # Timeline + controls
        self.timeline = TimelineWidget()
        root.addWidget(self.timeline)

        self.controls = PlaybackControls()
        root.addWidget(self.controls)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(HistoryDashboard(), "Metrics")
        self.tabs.addTab(EventTable(), "Events")
        self.tabs.addTab(ProcessSnapshotTable(), "Processes")
        root.addWidget(self.tabs)

        # --- Playback engine (mock) ---
        self.timer = QTimer()
        self.timer.timeout.connect(self.advance_timeline)

        self.controls.play.clicked.connect(self.timer.start)
        self.controls.pause.clicked.connect(self.timer.stop)

    def refresh_permissions(self):
        self.overlay.refresh()

    def advance_timeline(self):
        value = self.timeline.slider.value()
        self.timeline.slider.setValue(value + 1)
