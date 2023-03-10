"""Command line interfaces."""
from __future__ import annotations
import importlib

from ._deploy import cli as deploy
from ._service import cli as service
from ._migrate import cli as migrate
from ._server_map import cli as server_map

__all__ = ["deploy", "service", "migrate", "server_map"]


def __getattr__(name):
    return getattr(importlib.import_module(f"._{name}", __name__), "cli")
