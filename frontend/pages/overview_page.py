from PyQt6.QtWidgets import (
    QWidget,
    QGridLayout,
    QGroupBox,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QLabel,
    QProgressBar,
    QHBoxLayout
)


from frontend.graphs.cpu_graph import CPUGraph
from frontend.ui.widgets.network_widget import NetworkWidget

from frontend.ui.widgets.memory_bar import MemoryBar

from backend.interfaces.contexts import BridgeContext
from frontend.core.engine_bridge import EngineBridge


class OverviewPage(QWidget):

    def __init__(self, bridge: EngineBridge | None = None) -> None:

        super().__init__()

        self._bridge: EngineBridge | None = bridge


        grid = QGridLayout(self)



        # ======================
        # CPU GRAPH
        # ======================

        cpu_box = QGroupBox("CPU Usage")

        cpu_layout = QVBoxLayout(
            cpu_box
        )


        self.cpu = CPUGraph(bridge=self._bridge)

        self.cpu.setMinimumHeight(
            250
        )


        cpu_layout.addWidget(
            self.cpu
        )

        # ======================
        # CPU PER CORE
        # ======================

        cores_box = QGroupBox(
            "CPU Per Core"
        )

        cores_layout = QVBoxLayout(
            cores_box
        )

        self.core_bars = []
        self.core_labels = []
        self.temp_labels = []

        core_style = """

        QProgressBar {

            border: 1px solid #BFC7D5;
            border-radius: 5px;
            text-align: center;
            background-color: #F5F7FA;
            height: 16px;

        }


        QProgressBar::chunk {

            background-color: #4A90E2;
            border-radius: 4px;

        }

        """

        cpu = self._bridge.get_cpu_metrics()

        core_count = cpu["logical_cores"]

        if core_count == 0:
            core_count = len(cpu["per_core"])

        for i in range(core_count):
            row = QHBoxLayout()

            core_name = QLabel(
                f"Core {i}"
            )

            bar = QProgressBar()

            bar.setMaximum(100)

            bar.setStyleSheet(
                core_style
            )

            usage_label = QLabel(
                "0%"
            )

            temp_label = QLabel(
                "N/A°C"
            )

            row.addWidget(
                core_name
            )

            row.addWidget(
                bar
            )

            row.addWidget(
                usage_label
            )

            row.addWidget(
                temp_label
            )

            cores_layout.addLayout(
                row
            )

            self.core_bars.append(
                bar
            )

            self.core_labels.append(
                usage_label
            )

            self.temp_labels.append(
                temp_label
            )







        # ======================
        # MEMORY
        # ======================

        memory_box = QGroupBox(
            "Memory"
        )


        memory_layout = QVBoxLayout(
            memory_box
        )

        self.memory_bar = MemoryBar(bridge=self._bridge)

        self.memory_bar.setMaximumHeight(
            140
        )

        memory_layout.addWidget(
            self.memory_bar
        )



        # ======================
        # DISK
        # ======================

        disk_box = QGroupBox(
            "Disk Usage"
        )


        disk_layout = QVBoxLayout(
            disk_box
        )


        self.c_label = QLabel(
            "C:"
        )

        self.c_bar = QProgressBar()



        self.d_label = QLabel(
            "D:"
        )

        self.d_bar = QProgressBar()
        self.c_bar.setMaximumHeight(
            15
        )

        self.d_bar.setMaximumHeight(
            15
        )


        disk_style = """

        QProgressBar {

            border: 1px solid #BFC7D5;

            border-radius: 5px;

            text-align: center;

            background-color: #F5F7FA;

            height: 18px;

        }


        QProgressBar::chunk {

            background-color: #5B9DFF;

            border-radius: 4px;

        }

        """



        self.c_bar.setStyleSheet(
            disk_style
        )

        self.d_bar.setStyleSheet(
            disk_style
        )



        disk_layout.addWidget(
            self.c_label
        )


        disk_layout.addWidget(
            self.c_bar
        )


        disk_layout.addWidget(
            self.d_label
        )


        disk_layout.addWidget(
            self.d_bar
        )

        # ======================
        # NETWORK
        # ======================

        network_box = QGroupBox(
            "Network"
        )

        network_layout = QVBoxLayout(
            network_box
        )

        self.network_widget = NetworkWidget(bridge=self._bridge)

        self.network_widget.setMaximumHeight(
            140
        )

        network_layout.addWidget(
            self.network_widget
        )



        # ======================
        # PROCESS TABLE
        # ======================


        process_box = QGroupBox(
            "Processes"
        )


        process_layout = QVBoxLayout(
            process_box
        )


        self.create_process_table()


        process_layout.addWidget(
            self.table
        )

        # ======================
        # SYSTEM LOAD
        # ======================

        load_box = QGroupBox(
            "System Load"
        )

        load_layout = QVBoxLayout(
            load_box
        )

        self.load_cpu = QLabel()

        self.load_freq = QLabel()

        self.load_processes = QLabel()

        self.load_threads = QLabel()

        self.load_handles = QLabel()

        load_layout.addWidget(
            self.load_cpu
        )

        load_layout.addWidget(
            self.load_freq
        )

        load_layout.addWidget(
            self.load_processes
        )

        load_layout.addWidget(
            self.load_threads
        )

        load_layout.addWidget(
            self.load_handles
        )





        # ======================
        # GRID
        # ======================


        grid.addWidget(
            cpu_box,
            0,
            0,
            1,
            2
        )


        grid.addWidget(
            cores_box,
            0,
            2
        )


        grid.addWidget(
            memory_box,
            1,
            0
        )


        grid.addWidget(
            disk_box,
            1,
            1
        )


        grid.addWidget(
            network_box,
            1,
            2
        )


        grid.addWidget(
            process_box,
            2,
            0,
            1,
            2
        )


        grid.addWidget(
            load_box,
            2,
            2
        )



        grid.setColumnStretch(
            0,
            3
        )

        grid.setColumnStretch(
            1,
            3
        )

        grid.setColumnStretch(
            2,
            2
        )

        grid.setRowStretch(0, 4)
        grid.setRowStretch(1, 1)
        grid.setRowStretch(2, 5)



        # ======================
        # SIGNAL
        # ======================


        if self._bridge:
            self._bridge.state_updated.connect(self._on_state)



    def _on_state(self, ctx: BridgeContext) -> None:
        """Handle unified state update from EngineBridge signal."""
        self.update_cpu_cores()
        self.update_system_load()
        self.update_disks()
        self.update_processes()

    def update_disks(self):

        try:

            c = self._bridge.get_disk_usage(
                "C:\\"
            )


            self.c_bar.setValue(
                int(c["percent"])
            )


            self.c_label.setText(
                f"C: {c['used']/(1024**3):.0f} GB / {c['total']/(1024**3):.0f} GB"
            )


        except:

            pass



        try:

            d = self._bridge.get_disk_usage(
                "D:\\"
            )


            self.d_bar.setValue(
                int(d["percent"])
            )


            self.d_label.setText(
                f"D: {d['used']/(1024**3):.0f} GB / {d['total']/(1024**3):.0f} GB"
            )


        except:

            self.d_label.setText(
                "D: Not Found"
            )

    # def update_cpu_cores(self):
    #
    #     usage = self._bridge.get_cpu_metrics()["per_core"] or []
    #
    #     temperatures = []
    #
    #     try:
    #
    #         sensors = self._bridge.get_sensors()
    #
    #         if sensors:
    #
    #             for name, values in sensors.items():
    #
    #                 for value in values:
    #                     temperatures.append(
    #                         value
    #                     )
    def update_cpu_cores(self):

        cpu = self._bridge.get_cpu_metrics()

        usage = cpu["per_core"]

        for i, value in enumerate(usage):

            if i >= len(self.core_bars):
                break

            self.core_bars[i].setValue(int(value))
            self.core_labels[i].setText(f"{value:.1f}%")


        # except:
        #
        #     pass
        #
        # for i, value in enumerate(usage):
        #
        #     if i < len(self.core_bars):
        #
        #         self.core_bars[i].setValue(
        #             int(value)
        #         )
        #
        #         self.core_labels[i].setText(
        #             f"{value:.1f}%"
        #         )
        #
        #         if i < len(temperatures):
        #
        #             self.temp_labels[i].setText(
        #                 f"{temperatures[i]:.0f}°C"
        #             )
        #
        #         else:
        #
        #             self.temp_labels[i].setText(
        #                 "N/A°C"
        #             )

    def update_system_load(self):

        load = self._bridge.get_system_load()
        cpu = load["cpu_percent"]

        freq = self._bridge.get_cpu_metrics()["frequency"]

        processes = load["processes"]

        threads = load["threads"]

        handles = load["handles"]

        self.load_cpu.setText(
            f"CPU Load: {cpu:.1f}%"
        )

        if freq:

            self.load_freq.setText(
                f"CPU Frequency: {freq:.0f} MHz"
            )

        else:

            self.load_freq.setText(
                "CPU Frequency: N/A"
            )

        self.load_processes.setText(
            f"Processes: {processes}"
        )

        self.load_threads.setText(
            f"Threads: {threads}"
        )

        self.load_handles.setText(
            f"Handles: {handles}"
        )
    def create_process_table(self):

        self.table = QTableWidget()

        self.table.setColumnCount(6)

        self.table.setHorizontalHeaderLabels(
            [
                "PID",
                "Name",
                "CPU %",
                "Memory",
                "Status",
                "Threads"
            ]
        )

        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        self.table.setAlternatingRowColors(
            True
        )

        self.table.setSortingEnabled(
            True
        )



    def update_processes(self):

        processes = []

        for proc in self._bridge.get_process_list():

            try:

                memory = (
                        proc["memory_info"] /
                        (1024 ** 2)
                )

                processes.append(
                    [
                        proc["pid"],
                        proc["name"],
                        f"{proc['cpu_percent']:.1f}%",
                        f"{memory:.1f} MB",
                        proc["status"],
                        proc["num_threads"]
                    ]
                )


            except Exception:

                pass

        # sort by CPU usage

        processes.sort(
            key=lambda x: float(
                x[2].replace("%", "")
            ),
            reverse=True
        )

        # show top 20

        processes = processes[:20]

        self.table.setRowCount(
            len(processes)
        )

        for row, process in enumerate(processes):

            for col, value in enumerate(process):
                self.table.setItem(
                    row,
                    col,
                    QTableWidgetItem(
                        str(value)
                    )
                )

