# This file intentionally re-exports Python's stdlib logging so that any
# code doing `from utils import logging` still works, while NOT shadowing
# the stdlib module (renamed to log_manager.py).
from __future__ import annotations
import importlib as _il
import sys as _sys

# Force Python to load the real stdlib logging, not this file.
_real = _il.import_module('logging')
_sys.modules[__name__] = _real  # type: ignore
