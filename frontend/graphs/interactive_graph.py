import pyqtgraph as pg


class InteractiveGraph(
    pg.PlotWidget
):

    def __init__(self):

        super().__init__()

        self.showGrid(
            x=True,
            y=True
        )

        self.setMouseEnabled(
            x=True,
            y=True
        )

        self.setMenuEnabled(
            False
        )

        self.addLegend()

        self.crosshair_x = pg.InfiniteLine(
            angle=90
        )

        self.crosshair_y = pg.InfiniteLine(
            angle=0
        )

        self.addItem(
            self.crosshair_x
        )

        self.addItem(
            self.crosshair_y
        )