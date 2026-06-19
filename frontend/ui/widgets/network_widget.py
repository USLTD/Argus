from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout
)

from PyQt6.QtCore import QTimer

from frontend.core.engine_bridge import bridge
from frontend.graphs.base_graph import BaseGraph



class NetworkWidget(QWidget):

    def __init__(self):

        super().__init__()


        layout = QVBoxLayout(self)

        layout.setSpacing(0)
        layout.setContentsMargins(0,0,0,0)



        self.download_graph = BaseGraph(
            "Download MB/s"
        )

        self.download_graph.setFixedHeight(
            65
        )


        layout.addWidget(
            self.download_graph
        )



        self.upload_graph = BaseGraph(
            "Upload MB/s"
        )


        self.upload_graph.setFixedHeight(
            65
        )


        layout.addWidget(
            self.upload_graph
        )



        self.old = bridge.get_network_io()



        self.timer = QTimer()

        self.timer.timeout.connect(
            self.update_network
        )

        self.timer.start(
            1000
        )



    def update_network(self):

        new = bridge.get_network_io()



        download = (
            new["bytes_recv"] -
            self.old["bytes_recv"]
        )


        upload = (
            new["bytes_sent"] -
            self.old["bytes_sent"]
        )


        self.old = new



        self.download_graph.update_value(
            download/(1024**2)
        )


        self.upload_graph.update_value(
            upload/(1024**2)
        )