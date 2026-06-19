from PyQt6.QtCore import QTimer

from frontend.core.engine_bridge import bridge
from frontend.graphs.base_graph import BaseGraph



class CPUGraph(BaseGraph):

    def __init__(self):

        super().__init__(
            "CPU Usage %"
        )


        # Initialize cpu counter
        bridge.get_cpu_metrics()



        self.timer = QTimer()


        self.timer.timeout.connect(
            self.refresh
        )


        self.timer.start(
            1000
        )



    def refresh(self):

        cpu = bridge.get_cpu_metrics()["cpu_percent"]


        self.update_value(
            cpu
        )