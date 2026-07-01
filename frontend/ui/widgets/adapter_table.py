from PyQt6.QtWidgets import (
    QTableWidget,
    QTableWidgetItem
)

from frontend.core.engine_bridge import EngineBridge


class AdapterTable(QTableWidget):


    def __init__(self, bridge: EngineBridge | None = None):

        super().__init__()


        self.bridge = bridge

        self.previous_io = {}


        self.setColumnCount(9)

        self.setHorizontalHeaderLabels(
            [
                "Name",
                "Status",
                "IP",
                "MAC",
                "Download",
                "Upload",
                "Latency",
                "Gateway",
                "DNS"
            ]
        )


        self.setSortingEnabled(True)


        if self.bridge:
            self.bridge.state_updated.connect(self.update_table)



    def update_table(self, ctx):

        if self.bridge is None:
            return


        print("NETWORK TABLE UPDATE")

        adapters = self.bridge.get_network_interfaces()

        io_data = self.bridge.get_network_interfaces_io()

        print("ADAPTER DATA:", adapters)
        print("IO DATA:", io_data)


        self.setRowCount(len(adapters))


        for row, (name, info) in enumerate(adapters.items()):


            # ---------------- NAME ----------------
            self.setItem(row, 0, QTableWidgetItem(name))


            # ---------------- STATUS ----------------
            status = (
                "Connected"
                if info.get("status", False)
                else "Disconnected"
            )

            self.setItem(row, 1, QTableWidgetItem(status))


            # ---------------- IP ----------------
            self.setItem(
                row, 2,
                QTableWidgetItem(info.get("ip", "-"))
            )


            # ---------------- MAC ----------------
            self.setItem(
                row, 3,
                QTableWidgetItem(info.get("mac", "-"))
            )


            # ---------------- NETWORK SPEED ----------------

            adapter_io = io_data.get(
                name,
                {"bytes_sent": 0, "bytes_recv": 0}
            )


            download_kb = adapter_io["bytes_recv"] / 1024
            upload_kb = adapter_io["bytes_sent"] / 1024


            self.setItem(
                row, 4,
                QTableWidgetItem(f"{download_kb:.1f} KB/s")
            )

            self.setItem(
                row, 5,
                QTableWidgetItem(f"{upload_kb:.1f} KB/s")
            )


            # ---------------- PLACEHOLDERS ----------------
            self.setItem(row, 6, QTableWidgetItem("-"))
            self.setItem(row, 7, QTableWidgetItem("-"))
            self.setItem(row, 8, QTableWidgetItem("-"))