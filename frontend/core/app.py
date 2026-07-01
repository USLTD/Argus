from backend.storage.config import ArgusConfig
from frontend.core.engine_bridge import EngineBridge
import frontend.core.engine_bridge as _eb_mod
from frontend.ui.main_window import MainWindow


class ArgusApplication:

    def __init__(self, app, engine=None):
        self.app = app
        self.config = ArgusConfig()
        # Create EngineBridge and set as module-level singleton
        self.bridge = EngineBridge(engine=engine, config=self.config)
        _eb_mod.bridge = self.bridge
        self.window = MainWindow(bridge=self.bridge)

    def start(self):
        self.bridge.start_polling()
        self.window.show()

    def stop(self):
        self.bridge.stop_polling()