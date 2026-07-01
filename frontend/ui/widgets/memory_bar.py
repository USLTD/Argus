from PyQt6.QtWidgets import QWidget, QLabel, QProgressBar, QVBoxLayout

from backend.interfaces.contexts import BridgeContext
from frontend.core.engine_bridge import EngineBridge


class MemoryBar(QWidget):
    def __init__(self, bridge: EngineBridge | None = None) -> None:

        super().__init__()

        self._bridge: EngineBridge | None = bridge

        layout = QVBoxLayout(self)

        layout.setSpacing(2)
        layout.setContentsMargins(5, 5, 5, 5)

        style = """
        QProgressBar {
            border: 1px solid #BFC7D5;
            border-radius: 4px;
            text-align: center;
            background-color: #F5F7FA;
            height: 12px;
        }

        QProgressBar::chunk {
            background-color: #5B9DFF;
            border-radius: 3px;
        }
        """

        self.used_label = QLabel()
        self.used_bar = QProgressBar()

        self.cached_label = QLabel()
        self.cached_bar = QProgressBar()

        self.available_label = QLabel()
        self.available_bar = QProgressBar()

        self.free_label = QLabel()
        self.free_bar = QProgressBar()

        for bar in [self.used_bar, self.cached_bar, self.available_bar, self.free_bar]:
            bar.setMaximum(100)
            bar.setStyleSheet(style)

        layout.addWidget(self.used_label)
        layout.addWidget(self.used_bar)

        layout.addWidget(self.cached_label)
        layout.addWidget(self.cached_bar)

        layout.addWidget(self.available_label)
        layout.addWidget(self.available_bar)

        layout.addWidget(self.free_label)
        layout.addWidget(self.free_bar)

        if self._bridge:
            self._bridge.state_updated.connect(self._on_state)

    def _on_state(self, ctx: BridgeContext) -> None:
        self.refresh()

    def refresh(self):

        mem = self._bridge.get_memory_metrics()

        total = mem["total"]

        used = mem["used"]
        available = mem["available"]
        free = mem.get("free", mem["available"])

        cached = mem.get("cached", 0)

        self.used_label.setText(f"Used: {used / (1024**3):.1f} GB")

        self.cached_label.setText(f"Cached: {cached / (1024**3):.1f} GB")

        self.available_label.setText(f"Available: {available / (1024**3):.1f} GB")

        self.free_label.setText(f"Free: {free / (1024**3):.1f} GB")

        if total > 0:
            self.used_bar.setValue(int(used / total * 100))

            self.cached_bar.setValue(int(cached / total * 100))

            self.available_bar.setValue(int(available / total * 100))

            self.free_bar.setValue(int(free / total * 100))
        else:
            self.used_bar.setValue(0)
            self.cached_bar.setValue(0)
            self.available_bar.setValue(0)
            self.free_bar.setValue(0)
