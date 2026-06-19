from frontend.graphs.base_graph import BaseGraph


class MemoryGraph(BaseGraph):

    def __init__(self):

        super().__init__(
            "Memory Usage %"
        )

    def update_from_engine(self, ram_dict: dict) -> None:
        self.update_value(
            ram_dict.get("percent", 0.0)
        )