from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QSplitter,
    QShortcut,
    QLineEdit,
    QTextEdit
)
from PyQt5.QtGui import QKeySequence
from widgets.process_tree import ProcessTree


class ProcessesPage(QWidget):

    def __init__(self):
        super().__init__()

        # --- Shortcuts ---
        QShortcut(QKeySequence("Shift+K"), self, activated=self.mock_kill)
        QShortcut(QKeySequence("Shift+T"), self, activated=self.mock_terminate)
        QShortcut(QKeySequence("Shift+S"), self, activated=self.mock_signal)

        # --- Layout root ---
        root = QVBoxLayout(self)

        # Title
        title = QLabel("Process Explorer")
        title.setObjectName("PageTitle")
        root.addWidget(title)

        # Toolbar
        toolbar = QHBoxLayout()
        self.kill_btn = QPushButton("Kill")
        self.terminate_btn = QPushButton("Terminate")
        self.signal_btn = QPushButton("Signals")
        self.suspend_btn = QPushButton("Suspend")
        self.resume_btn = QPushButton("Resume")
        self.properties_btn = QPushButton("Properties")

        for btn in [
            self.kill_btn,
            self.terminate_btn,
            self.signal_btn,
            self.suspend_btn,
            self.resume_btn,
            self.properties_btn
        ]:
            toolbar.addWidget(btn)

        toolbar.addStretch()
        root.addLayout(toolbar)

        # Search filter
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search processes...")
        root.insertWidget(2, self.search)

        # Splitter
        splitter = QSplitter()

        self.process_tree = ProcessTree()
        splitter.addWidget(self.process_tree)

        # Details panel
        self.details = QTextEdit()
        self.details.setReadOnly(True)
        self.details.setHtml("""
        <h2>Process Details</h2>
        PID: 1524<br>
        Name: chrome.exe<br>
        Threads: 34<br>
        CPU: 8.4%<br>
        RAM: 1280 MB<br>
        Status: Running
        """)
        splitter.addWidget(self.details)

        splitter.setSizes([900, 300])
        root.addWidget(splitter)

        # Connect signals
        self.process_tree.itemClicked.connect(self.show_process_details)
        self.search.textChanged.connect(self.filter_processes)

    # --- Mock actions ---
    def mock_kill(self):
        print("Kill Process")

    def mock_terminate(self):
        print("Terminate Process")

    def mock_signal(self):
        print("Signal Process")

    # --- Details update ---
    def show_process_details(self, item):
        self.details.setHtml(f"""
        <h2>{item.text(1)}</h2>
        PID: {item.text(0)}<br>
        CPU: {item.text(2)}<br>
        RAM: {item.text(3)} MB<br>
        GPU: {item.text(4)} %<br>
        Threads: {item.text(7)}<br>
        User: {item.text(8)}<br>
        Status: {item.text(9)}
        """)

    # --- Search filter ---
    def filter_processes(self, text):
        text = text.lower()
        for i in range(self.process_tree.topLevelItemCount()):
            item = self.process_tree.topLevelItem(i)
            visible = text in item.text(1).lower()
            item.setHidden(not visible)
