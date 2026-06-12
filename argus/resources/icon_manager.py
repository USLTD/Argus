import qtawesome as qta


class IconManager:

    icons = {
        "overview": "fa5s.chart-line",
        "processes": "fa5s.tasks",
        "system": "fa5s.desktop",
        "network": "fa5s.network-wired",
        "memory": "fa5s.memory",
        "disk": "fa5s.hdd",
        "drivers": "fa5s.microchip",
        "scripts": "fa5s.code",
        "rules": "fa5s.gavel",
        "timemachine": "fa5s.history",
        "recording": "fa5s.video",
        "users": "fa5s.users",
        "settings": "fa5s.cog",
        "about": "fa5s.info-circle"
    }

    @staticmethod
    def get(name):
        return qta.icon(
            IconManager.icons.get(
                name,
                "fa5s.circle"
            ),
            color="white"
        )