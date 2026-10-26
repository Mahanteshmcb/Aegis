from backend import database as canonical_db
from backend import db as legacy_db


def test_canonical_database_single_source():
    assert getattr(legacy_db, "Base") is canonical_db.Base
    assert getattr(legacy_db, "engine") is canonical_db.engine
    assert getattr(legacy_db, "SessionLocal").kw["bind"] is canonical_db.engine
