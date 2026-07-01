import sqlite3
from datetime import datetime


class SQLiteHistory:

    def __init__(self, path="argus_history.db"):

        self.connection = sqlite3.connect(
            path
        )

        self.create_table()


    def create_table(self):

        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS system_history
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                timestamp TEXT NOT NULL,

                cpu REAL,
                memory REAL,
                disk REAL,

                network_sent INTEGER,
                network_recv INTEGER
            )
            """
        )

        self.connection.commit()


    def insert(self, snapshot):

        self.connection.execute(
            """
            INSERT INTO system_history
            (
                timestamp,
                cpu,
                memory,
                disk,
                network_sent,
                network_recv
            )

            VALUES (?, ?, ?, ?, ?, ?)

            """,
            (
                snapshot["timestamp"],
                snapshot["cpu"],
                snapshot["memory"],
                snapshot["disk"],
                snapshot["network_sent"],
                snapshot["network_recv"],
            )
        )

        self.connection.commit()

    def get_before(self, timestamp):
        cursor = self.connection.execute(
            """
            SELECT *
            FROM system_history
            WHERE timestamp <= ?
            ORDER BY timestamp DESC
            LIMIT 1
            """,
            (timestamp,)
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return {

            "timestamp": row[1],

            "cpu": row[2],

            "memory": row[3],

            "disk": row[4],

            "network_sent": row[5],

            "network_recv": row[6]
        }