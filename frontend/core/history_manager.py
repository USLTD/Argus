from datetime import datetime

from frontend.database.sqlite_history import SQLiteHistory



class HistoryManager:


    def __init__(self):

        self.database = SQLiteHistory()



    def save(self, context):

        data = context.data


        snapshot = {

            "timestamp":
                datetime.now().isoformat(),


            "cpu":
                data["cpu"]["cpu_percent"],


            "memory":
                data["memory"]["percent"],


            "disk":
                data["disks"][0]["percent"],


            "network_sent":
                data["network"]["bytes_sent"],


            "network_recv":
                data["network"]["bytes_recv"]

        }


        self.database.insert(snapshot)