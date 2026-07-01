from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem

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
                "DNS",
            ]
        )

        self.setSortingEnabled(True)

        if self.bridge:
            self.bridge.state_updated.connect(self.update_table)
        else:
            self.setRowCount(1)
            self.setItem(0, 0, QTableWidgetItem("No interfaces"))

    def update_table(self, ctx):

        if self.bridge is None:
            return

        def _load():
            adapters = self.bridge.get_network_interfaces()
            io_data_raw = self.bridge.get_network_io()
            return {
                "adapters": adapters,
                "io": io_data_raw,
            }

        def _on_loaded(result):
            if isinstance(result, Exception):
                print(f"Network load error: {result}")
                return

            adapters = result["adapters"]
            io_data_raw = result["io"]

            print("ADAPTER DATA:", adapters)
            print("IO DATA:", io_data_raw)

            try:
                self.setRowCount(len(adapters))
            except RuntimeError:
                return  # widget destroyed

            if not adapters:
                try:
                    self.setItem(0, 0, QTableWidgetItem("No interfaces"))
                except RuntimeError:
                    pass
                return

            for row, (name, info) in enumerate(adapters.items()):
                try:
                    # ---------------- NAME ----------------
                    self.setItem(row, 0, QTableWidgetItem(name))

                    # ---------------- STATUS ----------------
                    status = (
                        "Connected" if info.get("status", False) else "Disconnected"
                    )
                    self.setItem(row, 1, QTableWidgetItem(status))

                    # ---------------- IP ----------------
                    self.setItem(row, 2, QTableWidgetItem(info.get("ip", "-")))

                    # ---------------- MAC ----------------
                    self.setItem(row, 3, QTableWidgetItem(info.get("mac", "-")))

                    # ---------------- NETWORK SPEED ----------------
                    adapter_io = io_data_raw.get(
                        name, {"bytes_sent": 0, "bytes_recv": 0}
                    )

                    download_kb = adapter_io["bytes_recv"] / 1024
                    upload_kb = adapter_io["bytes_sent"] / 1024

                    self.setItem(row, 4, QTableWidgetItem(f"{download_kb:.1f} KB/s"))

                    self.setItem(row, 5, QTableWidgetItem(f"{upload_kb:.1f} KB/s"))

                    # ---------------- PLACEHOLDERS ----------------
                    self.setItem(row, 6, QTableWidgetItem("-"))
                    self.setItem(row, 7, QTableWidgetItem("-"))
                    self.setItem(row, 8, QTableWidgetItem("-"))
                except RuntimeError:
                    return  # widget destroyed mid-update

        self.bridge.run_async(_load, _on_loaded)
