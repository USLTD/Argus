from backend.core.engine import BackendEngine

from frontend.core.engine_bridge import EngineBridge
import frontend.core.engine_bridge as _eb_mod

from frontend.ui.main_window import MainWindow


class ArgusApplication:

    def __init__(self, app, engine=None):

        self.app = app

        if engine is None:
            engine = BackendEngine()

        self.engine = engine

        self.bridge = EngineBridge(engine=self.engine)

        _eb_mod.bridge = self.bridge

        self.window = MainWindow(bridge=self.bridge)

    def start(self):

        self.bridge.start_polling(1000)

        self.window.show()

    def stop(self):

        self.bridge.stop_polling()