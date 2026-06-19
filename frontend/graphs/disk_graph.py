from PyQt6.QtCore import QTimer

from frontend.core.engine_bridge import bridge
from frontend.graphs.base_graph import BaseGraph


class DiskGraph(BaseGraph):

    def __init__(self, drive):

        self.drive = drive

        title = f"{drive.replace(':\\\\', '')} Usage"

        super().__init__(title)

        self.graph.setYRange(0, 100)

        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh)
        self.timer.start(1000)

    def refresh(self):

        try:
            percent = bridge.get_disk_usage(
                self.drive
            )["percent"]

            self.update_value(percent)

        except Exception:
            pass