"""Command line interfaces."""
from __future__ import annotations
import importlib

__all__ = ["deploy", "service", "migrate"]


def __getattr__(name):
    return getattr(importlib.import_module(f"._{name}", __name__), "cli")
