"""Sandbox API injector (print, log, sleep, kill_process, …)."""

from backend.core.injectors import ApiInjector


def get_api_injector() -> ApiInjector:
    return ApiInjector(namespace_path="api")
