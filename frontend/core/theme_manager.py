from pathlib import Path


class ThemeManager:

    THEMES = {
        "light": "themes/light.qss",
        "dark": "themes/dark.qss",
    }

    @classmethod
    def apply_theme(cls, app, theme_name):

        path = Path(cls.THEMES[theme_name])

        if path.exists():
            app.setStyleSheet(path.read_text())