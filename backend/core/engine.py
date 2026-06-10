from typing import Any

from backend.core.loader import DiscoveryLoader
from backend.interfaces.caps import SystemMetrics
from backend.interfaces.plugins import PluginContext
from backend.interfaces.rules import build_compat_context
from backend.storage.config import ArgusConfig
from backend.storage.database import DatabaseManager


class BackendEngine:
    def __init__(self, db: DatabaseManager | None = None) -> None:
        self.config = ArgusConfig()
        self.db = db
        self.compat_ctx = build_compat_context()
        self.loader = DiscoveryLoader()
        self._ctx: PluginContext | None = None
        self.loader.soft_reload(compat_ctx=self.compat_ctx, config=self.config)
        self._init_active_plugins()

    def _init_active_plugins(self) -> None:
        self._ctx = PluginContext(
            config=self.config, db=self.db, driver=self.loader.active_driver
        )
        for script in self.loader.active_scripts:
            if hasattr(script, "trigger_load"):
                try:
                    script.trigger_load(self._ctx)
                except Exception as e:
                    print(f"Hook error [{script.METADATA.get('name', '?')}]: {e}")

    def get_system_state(self) -> dict[str, Any]:
        if not self.loader.active_driver:
            return {"error": "No valid driver loaded."}

        metrics: SystemMetrics = self.loader.active_driver.fetch_metrics()

        if self.db:
            self.db.write_snapshot(metrics)

        state = metrics.model_dump()

        for script in self.loader.active_scripts:
            try:
                script.execute_tick(state)
                if hasattr(script, "pop_output"):
                    for line in script.pop_output():
                        name = script.METADATA.get("name", "?")
                        print(f"[{name}] {line}")
            except Exception as e:
                print(f"Script Error [{script.METADATA.get('name', '?')}]: {e}")

        return state

    def trigger_soft_reload(self) -> None:
        if self._ctx:
            for script in self.loader.active_scripts:
                if hasattr(script, "trigger_unload"):
                    try:
                        script.trigger_unload(self._ctx)
                    except Exception:
                        pass

        self.loader.soft_reload(compat_ctx=self.compat_ctx, config=self.config)
        self._init_active_plugins()
