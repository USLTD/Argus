from PyQt5.QtWidgets import (
    QTreeWidget,
    QTreeWidgetItem
)


class HardwareTree(QTreeWidget):

    def __init__(self):
        super().__init__()

        self.setHeaderLabel(
            "Hardware Components"
        )

        self.populate()

    def populate(self):

        cpu = QTreeWidgetItem(["CPU"])
        cpu.addChild(
            QTreeWidgetItem(
                ["Intel Core Ultra 9"]
            )
        )

        gpu = QTreeWidgetItem(["GPU"])
        gpu.addChild(
            QTreeWidgetItem(
                ["NVIDIA RTX 5090"]
            )
        )

        motherboard = QTreeWidgetItem(
            ["Motherboard"]
        )

        motherboard.addChild(
            QTreeWidgetItem(
                ["ASUS ROG Maximus"]
            )
        )

        bios = QTreeWidgetItem(["BIOS"])
        bios.addChild(
            QTreeWidgetItem(
                ["AMI BIOS v2.1"]
            )
        )

        memory = QTreeWidgetItem(["Memory"])

        memory.addChild(
            QTreeWidgetItem(
                ["DDR5 Slot A"]
            )
        )

        memory.addChild(
            QTreeWidgetItem(
                ["DDR5 Slot B"]
            )
        )

        monitors = QTreeWidgetItem(
            ["Monitors"]
        )

        monitors.addChild(
            QTreeWidgetItem(
                ["LG UltraGear"]
            )
        )

        audio = QTreeWidgetItem(
            ["Audio"]
        )

        audio.addChild(
            QTreeWidgetItem(
                ["Realtek HD Audio"]
            )
        )

        self.addTopLevelItem(cpu)
        self.addTopLevelItem(gpu)
        self.addTopLevelItem(motherboard)
        self.addTopLevelItem(bios)
        self.addTopLevelItem(memory)
        self.addTopLevelItem(monitors)
        self.addTopLevelItem(audio)

        self.expandAll()