"""Compatibility layer for older imports that expect a database module.

The canonical SQLAlchemy registry lives in backend.database. This module does not
recreate its own engine or metadata; it delegates attribute access to the
canonical module so all services share one DB source of truth.
"""

from __future__ import annotations

import backend.database as _database


def __getattr__(name):
    if hasattr(_database, name):
        return getattr(_database, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def get_db():
    db = _database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


__all__ = ["Base", "SessionLocal", "engine", "get_db"]
