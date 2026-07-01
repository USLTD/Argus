from pathlib import Path


class ThemeManager:

    THEMES = {
        "dark": "frontend/themes/dark.qss",
    }

    @classmethod
    def apply_theme(cls, app, theme_name):

        if theme_name == "light":
            # Restore default Qt appearance
            app.setStyleSheet("")
            return

        path = Path(cls.THEMES[theme_name])

        if path.exists():
            app.setStyleSheet(
                path.read_text(encoding="utf-8")
            )