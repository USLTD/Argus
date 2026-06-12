from PyQt5.QtWidgets import (
    QTextEdit
)


class InfoPanel(QTextEdit):

    def __init__(self):
        super().__init__()

        self.setReadOnly(True)

        self.setHtml("""
        <h2>System Information</h2>

        Select an item
        from the hardware tree.
        """)

    def update_info(
            self,
            title
    ):

        self.setHtml(f"""
        <h2>{title}</h2>

        Manufacturer: Mock Vendor<br>
        Version: 1.0<br>
        Driver Date: 2025<br>
        Status: OK<br>
        Location: Device Manager<br>
        """)