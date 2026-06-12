from PyQt5.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QFrame
)

from widgets.graph_widget import GraphWidget


class StatCard(QFrame):

    def __init__(self, title):
        super().__init__()

        self.setObjectName("card")

        layout = QVBoxLayout(self)

        self.title = QLabel(title)

        self.value = QLabel("45 %")

        self.avg = QLabel("Average: 42 %")

        self.graph = GraphWidget()

        layout.addWidget(self.title)
        layout.addWidget(self.value)
        layout.addWidget(self.avg)
        layout.addWidget(self.graph)

        self.setMinimumHeight(250)

        self.graph.mouseDoubleClickEvent = (
            self.open_graph
        )

    def open_graph(
            self,
            event
    ):
        from widgets.graph_window import (
            GraphWindow
        )

        self.window = (
            GraphWindow()
        )

        self.window.show()