"""cu-perceive public surface.

Heavy deps (cv2 / PIL / win32) load lazily via PEP 562 __getattr__, so the
package imports anywhere — CLI help, `config` dump, tests, MCP bootstrap —
without a Windows/OpenCV environment. Only the commands that actually need
a dependency pull it in.
"""
from __future__ import annotations

__all__ = [
    "perceive",
    "find_window",
    "list_windows",
    "launch",
    "config",
]


def __getattr__(name: str):
    # importlib (not `from . import x`) so we never re-enter __getattr__ via hasattr.
    import importlib

    def _mod(mod: str):
        return importlib.import_module(f".{mod}", __name__)

    if name == "perceive":
        return _mod("core").perceive
    if name == "find_window":
        return _mod("windows").find_window
    if name == "list_windows":
        return _mod("windows").list_windows
    if name == "launch":
        return _mod("launch").launch
    if name == "config":
        return _mod("config")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
