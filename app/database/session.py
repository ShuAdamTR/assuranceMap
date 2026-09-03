from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy.orm import Session, sessionmaker

from app.database.engine import get_engine

SessionLocal = sessionmaker(autocommit=False, autoflush=False, future=True)

# Streamlit RerunException/StopException inherit BaseException (not Exception).
_STREAMLIT_CONTROL = {"RerunException", "StopException"}


def get_session() -> Session:
    return SessionLocal(bind=get_engine())


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    session = get_session()
    try:
        yield session
        session.commit()
    except BaseException as exc:
        if exc.__class__.__name__ in _STREAMLIT_CONTROL:
            session.commit()
            raise
        session.rollback()
        raise
    finally:
        session.close()
