"""Command line interfaces."""

from __future__ import annotations

import importlib

from ._deploy import cli as deploy
from ._migrate import cli as migrate

__all__ = ["deploy", "migrate"]


def __getattr__(name):
    return getattr(importlib.import_module(f"._{name}", __name__), "cli")
