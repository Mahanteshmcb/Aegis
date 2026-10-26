from sqlalchemy import text

from backend.database import _create_sqlite_engine


def test_file_sqlite_engine_uses_independent_pooled_connections(tmp_path):
    engine = _create_sqlite_engine(f"sqlite:///{tmp_path / 'pooled.db'}")
    try:
        with engine.connect() as first, engine.connect() as second:
            first_connection = first.connection.driver_connection
            second_connection = second.connection.driver_connection

            assert first_connection is not second_connection
            assert first.execute(text("SELECT 1")).scalar_one() == 1
            assert second.execute(text("SELECT 1")).scalar_one() == 1
    finally:
        engine.dispose()
