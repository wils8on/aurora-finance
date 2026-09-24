"""Session SQLAlchemy exclusiva por request."""

from collections.abc import Generator

from fastapi import Request
from sqlalchemy.orm import Session

from database.connection import SessionLocal

READ_ONLY_METHODS = {"GET", "HEAD", "OPTIONS"}


def get_session(request: Request) -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
        if request.method in READ_ONLY_METHODS:
            session.rollback()
        else:
            session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
