from pathlib import Path


class ThemeManager:

    @staticmethod
    def load_theme(
            app,
            theme_name
    ):

        file = (
            Path("themes")
            / f"{theme_name}.qss"
        )

        if file.exists():

            with open(
                file,
                "r",
                encoding="utf8"
            ) as f:

                app.setStyleSheet(
                    f.read()
                )