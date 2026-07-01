"""Custom user-provided drivers — auto-discovered by DiscoveryLoader.

To create a custom driver, add a new .py file in this directory with:
    1. A METADATA dict with \"compatible\" rules for platform matching
    2. A class inheriting from BaseDriver
    3. A module-level DRIVER = YourDriver assignment

Example:
    ```python
    from backend.interfaces.plugins import BaseDriver, PluginMeta
    from backend.interfaces.caps import SystemCapabilities
    from backend.interfaces.contexts import DriverContext
    from backend.interfaces.sentinels import Unavailable

    METADATA: PluginMeta = {
        \"name\": \"My Custom Driver\",
        \"author\": \"You\",
        \"version\": \"1.0\",
        \"compatible\": [
            \"sys.platform EQ 'linux' -> MEDIUM\",
        ],
    }

    class MyDriver(BaseDriver):
        def get_capabilities(self) -> SystemCapabilities:
            return SystemCapabilities()

        def manage_process(self, pid: int, action: str, **kwargs) -> bool:
            return False

    DRIVER = MyDriver
    ```
"""
