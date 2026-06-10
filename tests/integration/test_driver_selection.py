import sys

from backend.core.loader import DiscoveryLoader
from backend.interfaces.enums import ConfidenceScore


class TestDriverSelection:
    def test_windows_driver_wins_on_windows(self, compat_ctx) -> None:
        loader = DiscoveryLoader(".")
        loader.soft_reload(compat_ctx=compat_ctx)

        candidates = loader.all_candidates
        assert len(candidates) > 0

        if sys.platform == "win32":
            assert loader.active_driver is not None
            windows_candidates = [
                c for c in candidates if "Windows Driver" in c.meta["name"]
            ]
            assert len(windows_candidates) == 1
            assert windows_candidates[0].score == ConfidenceScore.FULL
            assert windows_candidates[0].loaded is True

    def test_linux_driver_reported_incompatible_on_windows(self, compat_ctx) -> None:
        if sys.platform != "win32":
            return

        loader = DiscoveryLoader(".")
        loader.soft_reload(compat_ctx=compat_ctx)

        linux_candidates = [
            c for c in loader.all_candidates if "Generic Linux Driver" in c.meta["name"]
        ]
        assert len(linux_candidates) == 1
        assert linux_candidates[0].score == ConfidenceScore.INCOMPATIBLE
        assert linux_candidates[0].loaded is False
