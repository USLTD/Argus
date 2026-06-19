from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QProgressBar,
    QFrame
)

from frontend.core.engine_bridge import bridge
from frontend.graphs.base_graph import BaseGraph


class DiskCard(QFrame):

    def __init__(self, drive):
        super().__init__()

        self.drive = drive

        self.setFrameShape(QFrame.Shape.Box)

        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #cfcfcf;
                border-radius: 6px;
            }

            QLabel {
                border: none;
                font-size: 11pt;
            }

            QProgressBar {
                height: 20px;
                text-align: center;
            }

            QProgressBar::chunk {
                background-color: #6aa9ff;
            }
        """)

        layout = QVBoxLayout(self)

        self.title_label = QLabel(f"{drive} Drive")
        self.title_label.setStyleSheet("""
            font-size: 14pt;
            font-weight: bold;
        """)

        self.space_label = QLabel("Loading...")

        self.progress_bar = QProgressBar()

        self.graph = BaseGraph("Usage History")
        self.graph.graph.setYRange(0, 100)

        layout.addWidget(self.title_label)
        layout.addWidget(self.space_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.graph)

        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh)
        self.timer.start(1000)

        self.refresh()

    def refresh(self):

        try:
            usage = bridge.get_disk_usage(self.drive)

            total_gb = usage["total"] / (1024 ** 3)
            used_gb = usage["used"] / (1024 ** 3)

            self.space_label.setText(
                f"{used_gb:.0f} GB / {total_gb:.0f} GB"
            )

            self.progress_bar.setValue(
                int(usage["percent"])
            )

            self.graph.update_value(
                usage["percent"]
            )

        except Exception:
            self.space_label.setText(
                "Drive not available"
            )


class DiskPage(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        # C Drive
        self.c_drive = DiskCard("C:\\")
        layout.addWidget(self.c_drive)

        # D Drive (optional)
        try:
            self.d_drive = DiskCard("D:\\")
            layout.addWidget(self.d_drive)
        except:
            pass