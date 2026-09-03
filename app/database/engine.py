from __future__ import annotations

from functools import lru_cache

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine

from app.config.settings import get_settings
from app.database.base import Base


@lru_cache
def get_engine() -> Engine:
    settings = get_settings()
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        future=True,
    )

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record) -> None:  # noqa: ARG001
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


def _migrate_sqlite(engine: Engine) -> None:
    """Additive SQLite migrations for existing local DBs."""
    with engine.begin() as conn:
        tables = {
            row[0]
            for row in conn.exec_driver_sql(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        if "reviews" not in tables:
            return
        cols = {
            row[1]
            for row in conn.exec_driver_sql("PRAGMA table_info(reviews)").fetchall()
        }
        if "examination_depth" not in cols:
            conn.exec_driver_sql(
                "ALTER TABLE reviews ADD COLUMN examination_depth "
                "VARCHAR(64) NOT NULL DEFAULT 'tam'"
            )


def init_db() -> None:
    # Import models so metadata is populated
    from app import models  # noqa: F401

    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    _migrate_sqlite(engine)

    from app.database.seed import seed_defaults

    seed_defaults()
