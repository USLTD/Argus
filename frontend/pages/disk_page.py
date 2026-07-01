from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QFrame

from frontend.graphs.base_graph import BaseGraph

from backend.interfaces.contexts import BridgeContext
from frontend.core.engine_bridge import EngineBridge


class DiskCard(QFrame):
    def __init__(self, drive: str, bridge: EngineBridge | None = None) -> None:
        super().__init__()

        self.drive = drive
        self._bridge: EngineBridge | None = bridge

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

        if self._bridge:
            self._bridge.state_updated.connect(self._on_state)

    def _on_state(self, ctx: BridgeContext) -> None:
        self.refresh()

    def refresh(self):

        try:
            usage = self._bridge.get_disk_usage(self.drive)

            total_gb = usage["total"] / (1024**3)
            used_gb = usage["used"] / (1024**3)

            self.space_label.setText(f"{used_gb:.0f} GB / {total_gb:.0f} GB")

            self.progress_bar.setValue(int(usage["percent"]))

            self.graph.update_value(usage["percent"])

        except Exception:
            self.space_label.setText("Drive not available")


class DiskPage(QWidget):
    def __init__(self, bridge: EngineBridge | None = None) -> None:
        super().__init__()

        self._bridge: EngineBridge | None = bridge

        layout = QVBoxLayout(self)

        # C Drive
        self.c_drive = DiskCard("C:\\", bridge=self._bridge)
        layout.addWidget(self.c_drive)

        # D Drive (optional)
        try:
            self.d_drive = DiskCard("D:\\", bridge=self._bridge)
            layout.addWidget(self.d_drive)
        except:
            pass
