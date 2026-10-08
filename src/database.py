from __future__ import annotations

import sys
from pathlib import Path

# Asegurar resolución de paquetes
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import backend.database as _backend_db
from backend.database import *  # noqa: F401, F403

# Reexportar todas las variables, funciones y clases de backend.database
for _key, _val in _backend_db.__dict__.items():
    if not _key.startswith("__"):
        globals()[_key] = _val

__all__ = [k for k in _backend_db.__dict__ if not k.startswith("__")]


def __getattr__(name: str):
    return getattr(_backend_db, name)
