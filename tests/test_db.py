import pytest
from datetime import datetime, timezone
from typing import Generator
import pandas as pd
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from fxml.data.db import get_engine, get_session
from fxml.data.models import Base, OHLCV
from fxml.data.loader import load_ohlcv


@pytest.fixture(scope="session")
def engine() -> Generator[Engine, None, None]:
    """Fixture to retrieve the SQLAlchemy engine."""
    eng = get_engine()
    assert isinstance(eng, Engine)
    # Ensure tables are created in the database for integration tests
    Base.metadata.create_all(bind=eng)
    yield eng


@pytest.fixture
def db_session(engine: Engine) -> Generator[Session, None, None]:
    """Fixture to provide a clean database session per test by truncating the ohlcv table."""
    with get_session() as session:
        # Clean the ohlcv table before each test
        session.query(OHLCV).delete()
        session.commit()

    with get_session() as session:
        yield session


def test_get_engine():
    """Verify that get_engine returns an Engine and can connect."""
    engine = get_engine()
    assert isinstance(engine, Engine)
    with engine.connect() as conn:
        assert conn is not None


def test_get_session():
    """Verify that get_session acts as a context manager and yields a Session."""
    with get_session() as session:
        assert isinstance(session, Session)


def test_ohlcv_model_creation(db_session: Session):
    """Verify we can create and retrieve an OHLCV record with all fields."""
    timestamp = datetime(2026, 7, 15, 12, 0, tzinfo=timezone.utc)
    record = OHLCV(
        pair="EUR/USD",
        interval="1h",
        timestamp=timestamp,
        open=1.1000,
        high=1.1050,
        low=1.0990,
        close=1.1020,
        volume=1500.0,
    )
    db_session.add(record)
    db_session.commit()

    retrieved = db_session.query(OHLCV).first()
    assert retrieved is not None
    assert retrieved.pair == "EUR/USD"
    assert retrieved.interval == "1h"
    # Compare timestamps (with tzinfo/UTC alignment)
    assert retrieved.timestamp.astimezone(timezone.utc) == timestamp
    assert retrieved.open == 1.1000
    assert retrieved.high == 1.1050
    assert retrieved.low == 1.0990
    assert retrieved.close == 1.1020
    assert retrieved.volume == 1500.0


def test_ohlcv_unique_constraint(db_session: Session):
    """Verify the UNIQUE(pair, interval, timestamp) constraint is enforced."""
    timestamp = datetime(2026, 7, 15, 12, 0, tzinfo=timezone.utc)

    record1 = OHLCV(
        pair="EUR/USD",
        interval="1h",
        timestamp=timestamp,
        open=1.1000,
        high=1.1050,
        low=1.0990,
        close=1.1020,
        volume=1500.0,
    )
    db_session.add(record1)
    db_session.commit()

    record2 = OHLCV(
        pair="EUR/USD",
        interval="1h",
        timestamp=timestamp,
        open=1.1010,
        high=1.1060,
        low=1.1000,
        close=1.1030,
        volume=1600.0,
    )
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=DeprecationWarning)
        warnings.filterwarnings("ignore", message="New instance.*conflicts with persistent instance", category=UserWarning)
        # SQLAlchemy emits an SAWarning (subclass of UserWarning) when the
        # identity-map detects a duplicate PK before the DB does.  We expect
        # this here because the whole point of the test is to verify the DB
        # constraint fires.
        from sqlalchemy.exc import SAWarning

        warnings.filterwarnings("ignore", category=SAWarning)
        db_session.add(record2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    db_session.rollback()


def test_load_ohlcv_success(db_session: Session):
    """Verify that load_ohlcv returns a sorted DataFrame matching the OHLCV schema."""
    t1 = datetime(2026, 7, 15, 10, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 7, 15, 11, 0, tzinfo=timezone.utc)
    t3 = datetime(2026, 7, 15, 12, 0, tzinfo=timezone.utc)

    # Insert out of order to test sorting
    records = [
        OHLCV(
            pair="EUR/USD",
            interval="1h",
            timestamp=t2,
            open=1.10,
            high=1.11,
            low=1.09,
            close=1.10,
            volume=100.0,
        ),
        OHLCV(
            pair="EUR/USD",
            interval="1h",
            timestamp=t1,
            open=1.09,
            high=1.10,
            low=1.08,
            close=1.09,
            volume=90.0,
        ),
        OHLCV(
            pair="EUR/USD",
            interval="1h",
            timestamp=t3,
            open=1.10,
            high=1.12,
            low=1.10,
            close=1.11,
            volume=110.0,
        ),
        # Insert a different pair/interval to ensure filtering works
        OHLCV(
            pair="GBP/USD",
            interval="1h",
            timestamp=t1,
            open=1.30,
            high=1.31,
            low=1.29,
            close=1.30,
            volume=80.0,
        ),
        OHLCV(
            pair="EUR/USD",
            interval="4h",
            timestamp=t1,
            open=1.09,
            high=1.11,
            low=1.08,
            close=1.10,
            volume=200.0,
        ),
    ]
    db_session.add_all(records)
    db_session.commit()

    df = load_ohlcv(pair="EUR/USD", interval="1h", session=db_session)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 3

    # Check expected columns
    expected_cols = ["timestamp", "open", "high", "low", "close", "volume"]
    for col in expected_cols:
        assert col in df.columns

    # Verify sorting by timestamp ascending
    timestamps = list(df["timestamp"])
    # Convert timestamps to UTC for comparison
    utc_timestamps = [
        t.astimezone(timezone.utc) if t.tzinfo else t.replace(tzinfo=timezone.utc)
        for t in timestamps
    ]
    assert utc_timestamps == [t1, t2, t3]

    # Verify values
    first_row = df.iloc[0]
    assert first_row["open"] == 1.09
    assert first_row["volume"] == 90.0


def test_load_ohlcv_date_filtering(db_session: Session):
    """Verify that load_ohlcv filters by start_date and end_date (inclusive)."""
    t1 = datetime(2026, 7, 15, 10, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 7, 15, 11, 0, tzinfo=timezone.utc)
    t3 = datetime(2026, 7, 15, 12, 0, tzinfo=timezone.utc)

    records = [
        OHLCV(
            pair="EUR/USD",
            interval="1h",
            timestamp=t1,
            open=1.0,
            high=1.0,
            low=1.0,
            close=1.0,
            volume=1.0,
        ),
        OHLCV(
            pair="EUR/USD",
            interval="1h",
            timestamp=t2,
            open=1.0,
            high=1.0,
            low=1.0,
            close=1.0,
            volume=1.0,
        ),
        OHLCV(
            pair="EUR/USD",
            interval="1h",
            timestamp=t3,
            open=1.0,
            high=1.0,
            low=1.0,
            close=1.0,
            volume=1.0,
        ),
    ]
    db_session.add_all(records)
    db_session.commit()

    # Query with start_date only
    df_start = load_ohlcv(
        pair="EUR/USD", interval="1h", start_date=t2, session=db_session
    )
    assert len(df_start) == 2

    # Query with end_date only
    df_end = load_ohlcv(pair="EUR/USD", interval="1h", end_date=t2, session=db_session)
    assert len(df_end) == 2

    # Query with both (narrow interval)
    df_both = load_ohlcv(
        pair="EUR/USD", interval="1h", start_date=t2, end_date=t2, session=db_session
    )
    assert len(df_both) == 1
    assert df_both.iloc[0]["timestamp"].astimezone(timezone.utc) == t2


def test_load_ohlcv_empty(db_session: Session):
    """Verify that load_ohlcv returns an empty DataFrame when no rows match."""
    df = load_ohlcv(pair="EUR/USD", interval="1h", session=db_session)
    assert isinstance(df, pd.DataFrame)
    assert df.empty
    expected_cols = ["timestamp", "open", "high", "low", "close", "volume"]
    for col in expected_cols:
        assert col in df.columns
