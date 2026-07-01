import socket
import getpass
import platform
import datetime

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGroupBox,
    QLabel,
    QGridLayout,
    QScrollArea,
)
from frontend.core.engine_bridge import EngineBridge


class SystemPage(QWidget):

    def __init__(self, bridge: EngineBridge | None = None) -> None:

        super().__init__()

        self._bridge: EngineBridge | None = bridge


        scroll = QScrollArea()

        scroll.setWidgetResizable(True)


        container = QWidget()

        layout = QVBoxLayout(container)


        scroll.setWidget(container)



        main_layout = QVBoxLayout(self)

        main_layout.addWidget(scroll)



        self.create_system_box(layout)

        self.create_cpu_box(layout)

        self.create_memory_box(layout)

        self.create_gpu_box(layout)

        self.create_board_box(layout)

        self.create_disk_box(layout)

        self.create_network_box(layout)

        self.create_battery_box(layout)



    # ======================
    # SYSTEM
    # ======================

    def create_system_box(self, layout):

        box = QGroupBox(
            "System Information"
        )


        grid = QGridLayout(box)



        boot = datetime.datetime.fromtimestamp(
            self._bridge.get_boot_time()
        )


        uptime = (
            datetime.datetime.now()
            -
            boot
        )


        data = {

            "Operating System":
            platform.platform(),

            "Computer Name":
            socket.gethostname(),

            "Username":
            getpass.getuser(),

            "Architecture":
            platform.architecture()[0],

            "Python Version":
            platform.python_version(),

            "Boot Time":
            str(boot),

            "Uptime":
            str(uptime).split(".")[0]

        }


        self.add_items(
            grid,
            data
        )


        layout.addWidget(box)



    # ======================
    # CPU
    # ======================

    def create_cpu_box(self, layout):

        box = QGroupBox(
            "CPU Information"
        )


        grid = QGridLayout(box)



        static = self._bridge.get_static_info()


        freq = self._bridge.get_cpu_metrics()["frequency"]



        data = {

            "CPU Model":
            static.get(
                "cpu", {}
            ).get(
                "name",
                "Unknown"
            ),


            "Physical Cores":
            self._bridge.get_cpu_metrics()["physical_cores"],


            "Logical Cores":
            self._bridge.get_cpu_metrics()["logical_cores"],


            "Frequency":
            f"{freq:.0f} MHz"
            if freq
            else "N/A",


            "Current Usage":
            f"{self._bridge.get_cpu_metrics()['cpu_percent']}%"

        }


        self.add_items(
            grid,
            data
        )


        layout.addWidget(box)




    # ======================
    # MEMORY
    # ======================

    def create_memory_box(self, layout):

        box = QGroupBox(
            "Memory"
        )


        grid = QGridLayout(box)

        mem = self._bridge.get_memory_metrics()

        if mem is None:
            mem = {
                "total": 0,
                "used": 0,
                "available": 0,
                "free": 0,
                "cached": 0,
                "percent": 0
            }



        data = {


            "Total RAM":
            f"{mem['total']/(1024**3):.2f} GB",


            "Used RAM":
            f"{mem['used']/(1024**3):.2f} GB",


            "Available RAM":
            f"{mem['available']/(1024**3):.2f} GB",


            "Usage":
            f"{mem['percent']}%"

        }



        self.add_items(
            grid,
            data
        )


        layout.addWidget(box)




    # ======================
    # GPU
    # ======================

    def create_gpu_box(self, layout):

        box = QGroupBox(
            "GPU"
        )


        grid = QGridLayout(box)


        static = self._bridge.get_static_info()
        gpu_raw = static.get("gpu", {})


        if gpu_raw and not gpu_raw.get("unavailable", False):


            data = {


                "Name":
                gpu_raw.get(
                    "name",
                    "Unknown"
                ),


                "Driver":
                gpu_raw.get(
                    "driver",
                    "Unknown"
                ),


                "Video Memory":
                (
                    f"{gpu_raw.get('vram_bytes', 0) / (1024**3):.2f} GB"
                    if gpu_raw.get("vram_bytes")
                    else "Unknown"
                ),

            }


            self.add_items(
                grid,
                data
            )


        else:


            grid.addWidget(
                QLabel(
                    "GPU information unavailable"
                )
            )



        layout.addWidget(box)





    # ======================
    # MOTHERBOARD BIOS
    # ======================

    def create_board_box(self, layout):

        box = QGroupBox(
            "Motherboard / BIOS"
        )


        grid = QGridLayout(box)



        static = self._bridge.get_static_info()
        board_raw = static.get("motherboard", {})


        if board_raw and not board_raw.get("unavailable", False):


            data = {


                "Manufacturer":
                board_raw.get(
                    "manufacturer",
                    "Unavailable"
                ),


                "Model":
                board_raw.get(
                    "model",
                    "Unavailable"
                ),


                "BIOS Version":
                board_raw.get(
                    "bios_version",
                    "Unavailable"
                ),

            }


            self.add_items(
                grid,
                data
            )


        else:


            grid.addWidget(
                QLabel(
                    "Unavailable"
                )
            )



        layout.addWidget(box)




    # ======================
    # DISKS
    # ======================

    def create_disk_box(self, layout):

        box = QGroupBox(
            "Storage"
        )


        grid = QGridLayout(box)



        row = 0



        for disk in self._bridge.get_disk_partitions():


            try:


                usage = self._bridge.get_disk_usage(
                    disk["mountpoint"]
                )



                grid.addWidget(
                    QLabel(
                        disk.get("device", disk["mountpoint"])
                    ),
                    row,
                    0
                )


                grid.addWidget(
                    QLabel(
                        f"{usage['used']/(1024**3):.1f} GB / "
                        f"{usage['total']/(1024**3):.1f} GB"
                    ),
                    row,
                    1
                )


                row += 1



            except:

                pass



        layout.addWidget(box)




    # ======================
    # NETWORK
    # ======================

    def create_network_box(self, layout):

        box = QGroupBox(
            "Network Adapters"
        )


        grid = QGridLayout(box)



        row = 0



        for name, addresses in self._bridge.get_network_interfaces().items():


            grid.addWidget(
                QLabel(name),
                row,
                0
            )

            ip = "N/A"

            for addr in addresses:

                if isinstance(addr, str):

                    if addr:
                        ip = addr

                else:

                    if addr.address:
                        ip = addr.address

            grid.addWidget(
                QLabel(str(ip)),
                row,
                1
            )
            break


        layout.addWidget(box)




    # ======================
    # BATTERY
    # ======================

    def create_battery_box(self, layout):

        box = QGroupBox(
            "Battery"
        )


        grid = QGridLayout(box)



        battery = self._bridge.get_battery()



        if battery:


            data = {


                "Charge":
                f"{battery['percent']}%",


                "Status":
                "Charging"
                if battery.get("power_plugged")
                else "Discharging"

            }



            self.add_items(
                grid,
                data
            )



        else:


            grid.addWidget(
                QLabel(
                    "No battery detected"
                )
            )



        layout.addWidget(box)




    # ======================
    # HELPER
    # ======================

    def add_items(self, grid, data):


        row = 0



        for key, value in data.items():


            grid.addWidget(
                QLabel(
                    str(key)
                ),
                row,
                0
            )


            grid.addWidget(
                QLabel(
                    str(value)
                ),
                row,
                1
            )


            row += 1