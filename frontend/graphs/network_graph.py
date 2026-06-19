from PyQt6.QtCore import QTimer

from frontend.core.engine_bridge import bridge
from frontend.graphs.base_graph import BaseGraph


class NetworkGraph(BaseGraph):

    def __init__(self):

        super().__init__(
            "Network Activity (MB/s)"
        )

        self.old_data = bridge.get_network_io()

        self.graph.setYRange(
            0,
            10
        )

        self.timer = QTimer()

        self.timer.timeout.connect(
            self.refresh
        )

        self.timer.start(1000)


    def refresh(self):

        new_data = bridge.get_network_io()


        download = (
            new_data["bytes_recv"] -
            self.old_data["bytes_recv"]
        )


        self.old_data = new_data


        # convert bytes -> MB

        download_mb = download / (1024 ** 2)


        # show download activity

        self.update_value(
            download_mb
        )