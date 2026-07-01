import json
from datetime import datetime

from frontend.database.sqlite_history import SQLiteHistory


class HistoryManager:
    def __init__(self):

        self.database = SQLiteHistory()

    def save(self, context):

        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "data": context.data,
        }

        self.database.insert(snapshot)

    def get_snapshot(self, timestamp: str) -> dict | None:
        return self.database.get_before(timestamp)
