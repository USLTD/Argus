import json


class SettingsManager:
    FILE = "settings.json"

    @classmethod
    def load(cls):

        try:
            with open(cls.FILE, "r") as f:
                return json.load(f)

        except:
            return {}

    @classmethod
    def save(cls, data):

        with open(cls.FILE, "w") as f:
            json.dump(data, f, indent=4)
