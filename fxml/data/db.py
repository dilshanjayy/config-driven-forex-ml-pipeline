from contextlib import contextmanager
import os
from typing import Generator
from dotenv import load_dotenv
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, DeclarativeBase

# Load environment variables from .env file
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

_engine: Engine | None = None


def get_engine() -> Engine:
    """Retrieve the SQLAlchemy engine, creating it if it doesn't exist."""
    global _engine
    if not _engine:
        if not DATABASE_URL:
            raise ValueError("Database URL is not set in the environment variables.")
        _engine = create_engine(DATABASE_URL)
    return _engine


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Create a new SQLAlchemy session and ensure it is properly closed after use."""
    session = Session(bind=get_engine(), autoflush=False, autocommit=False)

    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass
