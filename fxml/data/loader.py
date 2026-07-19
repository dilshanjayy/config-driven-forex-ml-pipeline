from datetime import datetime
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import select

from fxml.data.models import OHLCV
from fxml.data.db import get_session


def load_ohlcv(
    pair: str,
    interval: str,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    session: Session | None = None,
):
    """Load OHLCV data from the database for a given pair and interval within a specified date range."""

    def _execute_query(session: Session) -> pd.DataFrame:
        stmt = select(OHLCV).where(OHLCV.pair == pair, OHLCV.interval == interval)

        # Filter by date range if provided
        if start_date:
            stmt = stmt.where(OHLCV.timestamp >= start_date)
        if end_date:
            stmt = stmt.where(OHLCV.timestamp <= end_date)

        # Order by timestamp to ensure the data is in chronological order
        stmt = stmt.order_by(OHLCV.timestamp)

        results = session.execute(stmt)
        records = results.scalars().all()

        df = pd.DataFrame(
            [
                {
                    "timestamp": r.timestamp,
                    "open": r.open,
                    "high": r.high,
                    "low": r.low,
                    "close": r.close,
                    "volume": r.volume,
                }
                for r in records
            ],
            columns=[
                "timestamp",
                "open",
                "high",
                "low",
                "close",
                "volume",
            ],
        )

        return df

    if session is not None:
        return _execute_query(session)

    with get_session() as session:
        return _execute_query(session)
