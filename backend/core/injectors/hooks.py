"""Lifecycle hook injectors (on_load, on_unload)."""

from backend.core.injectors import EventInjector


def get_hooks_injector() -> EventInjector:
    return EventInjector(
        namespace_path="lifecycle",
        events=["on_load", "on_unload"],
    )
