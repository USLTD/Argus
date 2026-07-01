import json
import sqlite3


class SQLiteHistory:
    def __init__(self, path="argus_history.db"):

        self.connection = sqlite3.connect(path)

        self.create_table()

    def create_table(self):

        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS metric_snapshots
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                timestamp TEXT NOT NULL,

                data TEXT NOT NULL
            )
            """
        )

        self.connection.commit()

    def insert(self, snapshot):

        self.connection.execute(
            """
            INSERT INTO metric_snapshots
            (
                timestamp,
                data
            )

            VALUES (?, ?)

            """,
            (
                snapshot["timestamp"],
                json.dumps(snapshot["data"]),
            ),
        )

        self.connection.commit()

    def get_before(self, timestamp):
        cursor = self.connection.execute(
            """
            SELECT id, timestamp, data
            FROM metric_snapshots
            WHERE timestamp <= ?
            ORDER BY timestamp DESC
            LIMIT 1
            """,
            (timestamp,),
        )

        row = cursor.fetchone()

        if row is None:
            return None

        data = json.loads(row[2])  # row[2] = the data column
        data["timestamp"] = row[1]  # row[1] = the timestamp column
        return data
