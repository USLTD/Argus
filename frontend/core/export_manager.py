from PyQt6.QtWidgets import QFileDialog


class ExportManager:

    @staticmethod
    def export_csv(widget):

        path, _ = QFileDialog.getSaveFileName(
            None,
            "Export CSV",
            "",
            "*.csv"
        )

        if not path:
            return

        with open(
            path,
            "w"
        ) as f:

            f.write(
                "ARGUS Export\n"
            )