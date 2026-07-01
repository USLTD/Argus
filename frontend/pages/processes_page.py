from PyQt6.QtGui import QShortcut, QKeySequence

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QPushButton,
    QLineEdit,
    QLabel,
    QMessageBox,
)

from backend.interfaces.contexts import BridgeContext
from frontend.core.engine_bridge import EngineBridge


class ProcessesPage(QWidget):

    def __init__(self, bridge: EngineBridge | None = None) -> None:

        super().__init__()

        self._bridge: EngineBridge | None = bridge


        layout = QVBoxLayout(self)



        # ======================
        # SEARCH
        # ======================

        top = QHBoxLayout()


        self.search = QLineEdit()

        self.search.setPlaceholderText(
            "Search process..."
        )


        self.search.textChanged.connect(
            self.filter_processes
        )


        top.addWidget(
            QLabel("Search:")
        )


        top.addWidget(
            self.search
        )


        layout.addLayout(
            top
        )



        # ======================
        # TABLE
        # ======================


        self.table = QTableWidget()


        self.table.setColumnCount(10)


        self.table.setHorizontalHeaderLabels(
            [
                "PID",
                "Name",
                "CPU %",
                "Memory MB",
                "Status",
                "Threads",
                "User",
                "Parent PID",
                "Create Time",
                "Path"
            ]
        )


        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )


        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )


        self.table.setSortingEnabled(
            True
        )


        layout.addWidget(
            self.table
        )



        # ======================
        # BUTTONS
        # ======================


        buttons = QHBoxLayout()



        self.refresh_btn = QPushButton(
            "Refresh (F5)"
        )

        self.refresh_btn.clicked.connect(
            self.load_processes
        )



        self.terminate_btn = QPushButton(
            "Terminate (Shift + T)"
        )

        self.terminate_btn.clicked.connect(
            self.terminate_process
        )



        self.kill_btn = QPushButton(
            "Kill (Shift + K)"
        )

        self.kill_btn.clicked.connect(
            self.kill_process
        )



        buttons.addWidget(
            self.refresh_btn
        )

        buttons.addWidget(
            self.terminate_btn
        )

        buttons.addWidget(
            self.kill_btn
        )


        layout.addLayout(
            buttons
        )



        # ======================
        # DATA
        # ======================


        self.process_data = []



        # ======================
        # SIGNAL
        # ======================


        if self._bridge:
            self._bridge.state_updated.connect(self._on_state)

        # ======================
        # SHORTCUTS
        # ======================

        # Refresh
        QShortcut(
            QKeySequence("F5"),
            self
        ).activated.connect(
            self.load_processes
        )

        # Refresh
        QShortcut(
            QKeySequence("Ctrl+R"),
            self
        ).activated.connect(
            self.load_processes
        )

        # Kill process
        # Shift + K

        QShortcut(
            QKeySequence("Shift+K"),
            self
        ).activated.connect(
            self.kill_process
        )

        # Terminate process
        # Shift + T

        QShortcut(
            QKeySequence("Shift+T"),
            self
        ).activated.connect(
            self.terminate_process
        )

        # Clear selection

        QShortcut(
            QKeySequence("Escape"),
            self
        ).activated.connect(
            self.table.clearSelection
        )



    # ======================
    # LOAD PROCESSES
    # ======================


    def _on_state(self, ctx: BridgeContext) -> None:
        self.load_processes()

    def load_processes(self):

        self.process_data.clear()


        for proc in self._bridge.get_process_list():

            try:

                memory = (
                    proc["memory_info"] /
                    (1024**2)
                )



                self.process_data.append(
                    {
                        "pid": proc["pid"],
                        "values":
                        [
                            proc["pid"],
                            proc["name"],
                            f"{proc['cpu_percent']:.1f}",
                            f"{memory:.1f}",
                            proc["status"],
                            proc["num_threads"],
                            proc.get("username", ""),
                            proc.get("ppid", ""),
                            proc.get("create_time", ""),
                            proc.get("exe", "")
                        ]
                    }
                )


            except Exception:

                pass



        self.display_processes(
            self.process_data
        )



    # ======================
    # DISPLAY
    # ======================


    def display_processes(
        self,
        data
    ):


        self.table.setRowCount(
            len(data)
        )


        for row, proc in enumerate(data):


            for col, value in enumerate(
                proc["values"]
            ):

                self.table.setItem(
                    row,
                    col,
                    QTableWidgetItem(
                        str(value)
                    )
                )



    # ======================
    # SEARCH FILTER
    # ======================


    def filter_processes(
        self,
        text
    ):

        text = text.lower()


        filtered = []


        for proc in self.process_data:


            if text in str(
                proc["values"][1]
            ).lower():

                filtered.append(
                    proc
                )


        self.display_processes(
            filtered
        )



    # ======================
    # GET SELECTED PID
    # ======================


    def selected_pid(self):

        row = (
            self.table.currentRow()
        )


        if row < 0:
            return None


        return int(
            self.table.item(
                row,
                0
            ).text()
        )



    # ======================
    # TERMINATE
    # ======================


    def terminate_process(self):

        pid = self.selected_pid()


        if pid:

            try:

                self._bridge.terminate_process(
                    pid
                )


            except Exception as e:

                QMessageBox.warning(
                    self,
                    "Error",
                    str(e)
                )



    # ======================
    # KILL
    # ======================


    def kill_process(self):

        pid = self.selected_pid()


        if pid:

            try:

                self._bridge.kill_process(
                    pid
                )


            except Exception as e:

                QMessageBox.warning(
                    self,
                    "Error",
                    str(e)
                )