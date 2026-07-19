from fxml.data.db import Base
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
import sqlalchemy as sa


class OHLCV(Base):
    __tablename__ = "ohlcv"

    pair: Mapped[str] = mapped_column(primary_key=True)
    interval: Mapped[str] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), primary_key=True
    )
    open: Mapped[float] = mapped_column(nullable=False)
    high: Mapped[float] = mapped_column(nullable=False)
    low: Mapped[float] = mapped_column(nullable=False)
    close: Mapped[float] = mapped_column(nullable=False)
    volume: Mapped[float] = mapped_column(nullable=False, default=0.0)

    DATAFRAME_COLUMNS: list[str] = [
        "timestamp",
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]

    def to_dict(self) -> dict:
        """Return the OHLCV data columns as a dictionary for DataFrame construction."""
        return {col: getattr(self, col) for col in self.DATAFRAME_COLUMNS}
