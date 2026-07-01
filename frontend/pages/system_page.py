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
from backend.interfaces.contexts import BridgeContext


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


        if self._bridge:
            self._bridge.state_updated.connect(self._on_state)


    # ======================
    # SYSTEM
    # ======================

    def create_system_box(self, layout):

        box = QGroupBox(
            "System Information"
        )

        grid = QGridLayout(box)

        row = 0
        grid.addWidget(QLabel("Operating System"), row, 0)
        grid.addWidget(QLabel(platform.platform()), row, 1)
        row += 1
        grid.addWidget(QLabel("Computer Name"), row, 0)
        grid.addWidget(QLabel(socket.gethostname()), row, 1)
        row += 1
        grid.addWidget(QLabel("Username"), row, 0)
        grid.addWidget(QLabel(getpass.getuser()), row, 1)
        row += 1
        grid.addWidget(QLabel("Architecture"), row, 0)
        grid.addWidget(QLabel(platform.architecture()[0]), row, 1)
        row += 1
        grid.addWidget(QLabel("Python Version"), row, 0)
        grid.addWidget(QLabel(platform.python_version()), row, 1)
        row += 1
        grid.addWidget(QLabel("Boot Time"), row, 0)
        self._boot_time_label = QLabel("Loading...")
        grid.addWidget(self._boot_time_label, row, 1)
        row += 1
        grid.addWidget(QLabel("Uptime"), row, 0)
        self._uptime_label = QLabel("Loading...")
        grid.addWidget(self._uptime_label, row, 1)

        layout.addWidget(box)



    # ======================
    # CPU
    # ======================

    def create_cpu_box(self, layout):

        box = QGroupBox(
            "CPU Information"
        )

        grid = QGridLayout(box)

        row = 0
        grid.addWidget(QLabel("CPU Model"), row, 0)
        self._cpu_name_label = QLabel("Loading...")
        grid.addWidget(self._cpu_name_label, row, 1)
        row += 1
        grid.addWidget(QLabel("Physical Cores"), row, 0)
        self._cpu_physical_label = QLabel("Loading...")
        grid.addWidget(self._cpu_physical_label, row, 1)
        row += 1
        grid.addWidget(QLabel("Logical Cores"), row, 0)
        self._cpu_logical_label = QLabel("Loading...")
        grid.addWidget(self._cpu_logical_label, row, 1)
        row += 1
        grid.addWidget(QLabel("Frequency"), row, 0)
        self._cpu_freq_label = QLabel("Loading...")
        grid.addWidget(self._cpu_freq_label, row, 1)
        row += 1
        grid.addWidget(QLabel("Current Usage"), row, 0)
        self._cpu_usage_label = QLabel("Loading...")
        grid.addWidget(self._cpu_usage_label, row, 1)

        layout.addWidget(box)



    # ======================
    # MEMORY
    # ======================

    def create_memory_box(self, layout):

        box = QGroupBox(
            "Memory"
        )

        grid = QGridLayout(box)

        row = 0
        grid.addWidget(QLabel("Total RAM"), row, 0)
        self._mem_total_label = QLabel("Loading...")
        grid.addWidget(self._mem_total_label, row, 1)
        row += 1
        grid.addWidget(QLabel("Used RAM"), row, 0)
        self._mem_used_label = QLabel("Loading...")
        grid.addWidget(self._mem_used_label, row, 1)
        row += 1
        grid.addWidget(QLabel("Available RAM"), row, 0)
        self._mem_available_label = QLabel("Loading...")
        grid.addWidget(self._mem_available_label, row, 1)
        row += 1
        grid.addWidget(QLabel("Usage"), row, 0)
        self._mem_usage_label = QLabel("Loading...")
        grid.addWidget(self._mem_usage_label, row, 1)

        layout.addWidget(box)



    # ======================
    # GPU
    # ======================

    def create_gpu_box(self, layout):

        box = QGroupBox(
            "GPU"
        )

        grid = QGridLayout(box)

        row = 0
        grid.addWidget(QLabel("Name"), row, 0)
        self._gpu_name_label = QLabel("Loading...")
        grid.addWidget(self._gpu_name_label, row, 1)
        row += 1
        grid.addWidget(QLabel("Driver"), row, 0)
        self._gpu_driver_label = QLabel("Loading...")
        grid.addWidget(self._gpu_driver_label, row, 1)
        row += 1
        grid.addWidget(QLabel("Video Memory"), row, 0)
        self._gpu_vram_label = QLabel("Loading...")
        grid.addWidget(self._gpu_vram_label, row, 1)

        layout.addWidget(box)



    # ======================
    # MOTHERBOARD BIOS
    # ======================

    def create_board_box(self, layout):

        box = QGroupBox(
            "Motherboard / BIOS"
        )

        grid = QGridLayout(box)

        row = 0
        grid.addWidget(QLabel("Manufacturer"), row, 0)
        self._board_manufacturer_label = QLabel("Loading...")
        grid.addWidget(self._board_manufacturer_label, row, 1)
        row += 1
        grid.addWidget(QLabel("Model"), row, 0)
        self._board_model_label = QLabel("Loading...")
        grid.addWidget(self._board_model_label, row, 1)
        row += 1
        grid.addWidget(QLabel("BIOS Version"), row, 0)
        self._board_bios_label = QLabel("Loading...")
        grid.addWidget(self._board_bios_label, row, 1)

        layout.addWidget(box)




    # ======================
    # DISKS
    # ======================

    def create_disk_box(self, layout):

        box = QGroupBox(
            "Storage"
        )

        self._disk_grid = QGridLayout(box)
        self._disk_grid.addWidget(
            QLabel("Loading disk information...")
        )

        layout.addWidget(box)




    # ======================
    # NETWORK
    # ======================

    def create_network_box(self, layout):

        box = QGroupBox(
            "Network Adapters"
        )

        self._network_grid = QGridLayout(box)
        self._network_grid.addWidget(
            QLabel("Loading network information...")
        )

        layout.addWidget(box)




    # ======================
    # BATTERY
    # ======================

    def create_battery_box(self, layout):

        box = QGroupBox(
            "Battery"
        )

        grid = QGridLayout(box)

        row = 0
        grid.addWidget(QLabel("Charge"), row, 0)
        self._battery_charge_label = QLabel("Loading...")
        grid.addWidget(self._battery_charge_label, row, 1)
        row += 1
        grid.addWidget(QLabel("Status"), row, 0)
        self._battery_status_label = QLabel("Loading...")
        grid.addWidget(self._battery_status_label, row, 1)
        layout.addWidget(box)


    # ======================
    # SIGNAL / REFRESH
    # ======================

    def _on_state(self, ctx: BridgeContext) -> None:
        """Handle unified state update from EngineBridge signal."""
        self.refresh()

    def refresh(self) -> None:
        """Refresh all bridge-dependent labels with current data."""

        if not self._bridge:
            return

        static = self._bridge.get_static_info()

        # --- System ---
        boot = datetime.datetime.fromtimestamp(
            self._bridge.get_boot_time()
        )
        uptime = datetime.datetime.now() - boot
        self._boot_time_label.setText(str(boot))
        self._uptime_label.setText(str(uptime).split(".")[0])

        # --- CPU ---
        cpu_metrics = self._bridge.get_cpu_metrics()
        cpu = static.get("cpu", {})
        freq = cpu_metrics["frequency"]
        self._cpu_name_label.setText(
            cpu.get("name", "Unknown")
        )
        self._cpu_physical_label.setText(
            str(cpu_metrics["physical_cores"])
        )
        self._cpu_logical_label.setText(
            str(cpu_metrics["logical_cores"])
        )
        self._cpu_freq_label.setText(
            f"{freq:.0f} MHz" if freq else "N/A"
        )
        self._cpu_usage_label.setText(
            f"{cpu_metrics['cpu_percent']}%"
        )

        # --- Memory ---
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
        self._mem_total_label.setText(
            f"{mem['total']/(1024**3):.2f} GB"
        )
        self._mem_used_label.setText(
            f"{mem['used']/(1024**3):.2f} GB"
        )
        self._mem_available_label.setText(
            f"{mem['available']/(1024**3):.2f} GB"
        )
        self._mem_usage_label.setText(
            f"{mem['percent']}%"
        )

        # --- GPU ---
        gpu_raw = static.get("gpu", {})
        if gpu_raw and not gpu_raw.get("unavailable", False):
            self._gpu_name_label.setText(
                gpu_raw.get("name", "Unknown")
            )
            self._gpu_driver_label.setText(
                gpu_raw.get("driver", "Unknown")
            )
            self._gpu_vram_label.setText(
                (
                    f"{gpu_raw.get('vram_bytes', 0) / (1024**3):.2f} GB"
                    if gpu_raw.get("vram_bytes")
                    else "Unknown"
                )
            )
        else:
            self._gpu_name_label.setText("Unavailable")
            self._gpu_driver_label.setText("Unavailable")
            self._gpu_vram_label.setText("Unavailable")

        # --- Motherboard ---
        board_raw = static.get("motherboard", {})
        if board_raw and not board_raw.get("unavailable", False):
            self._board_manufacturer_label.setText(
                board_raw.get("manufacturer", "Unavailable")
            )
            self._board_model_label.setText(
                board_raw.get("model", "Unavailable")
            )
            self._board_bios_label.setText(
                board_raw.get("bios_version", "Unavailable")
            )
        else:
            self._board_manufacturer_label.setText("Unavailable")
            self._board_model_label.setText("Unavailable")
            self._board_bios_label.setText("Unavailable")

        # --- Disks ---
        self._clear_grid(self._disk_grid)
        row = 0
        for disk in self._bridge.get_disk_partitions():
            try:
                usage = self._bridge.get_disk_usage(
                    disk["mountpoint"]
                )
                self._disk_grid.addWidget(
                    QLabel(
                        disk.get("device", disk["mountpoint"])
                    ),
                    row,
                    0
                )
                self._disk_grid.addWidget(
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

        # --- Network ---
        self._clear_grid(self._network_grid)
        row = 0
        for name, addresses in self._bridge.get_network_interfaces().items():
            self._network_grid.addWidget(
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
            self._network_grid.addWidget(
                QLabel(str(ip)),
                row,
                1
            )
            break

        # --- Battery ---
        battery = self._bridge.get_battery()
        if battery:
            self._battery_charge_label.setText(
                f"{battery['percent']}%"
            )
            self._battery_status_label.setText(
                "Charging"
                if battery.get("power_plugged")
                else "Discharging"
            )
        else:
            self._battery_charge_label.setText("N/A")
            self._battery_status_label.setText("No battery detected")

    @staticmethod
    def _clear_grid(grid: QGridLayout) -> None:
        """Remove all items from a QGridLayout."""
        while grid.count():
            item = grid.takeAt(0)
            if item:
                widget = item.widget()
                if widget:
                    widget.deleteLater()

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