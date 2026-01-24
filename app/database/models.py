"""
Database models for storing cryptocurrency price data.
"""

from datetime import UTC, datetime
from typing import Self

from sqlalchemy import BigInteger, DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base


class PriceTick(Base):
    """
    Model for storing cryptocurrency price ticks.

    Stores timestamped price data for different tickers with index prices
    from Deribit exchange.

    Attributes:
        id: Primary key identifier.
        ticker: Cryptocurrency ticker symbol (e.g., 'btc_usd', 'eth_usd').
        price: Current index price in USD.
        timestamp: UNIX timestamp when price was recorded.
        created_at: Database record creation timestamp.
    """

    __tablename__ = "price_ticks"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )
    ticker: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )
    price: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    timestamp: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        """String representation of PriceTick."""
        return (
            f"PriceTick(id={self.id}, ticker={self.ticker}, "
            f"price={self.price}, timestamp={self.timestamp})"
        )

    @classmethod
    def create(
        cls,
        ticker: str,
        price: float,
        timestamp: int | None = None,
    ) -> Self:
        """
        Factory method to create PriceTick instance.

        Args:
            ticker: Cryptocurrency ticker symbol.
            price: Current price in USD.
            timestamp: UNIX timestamp (defaults to current time).

        Returns:
            PriceTick instance.
        """
        if timestamp is None:
            timestamp = int(datetime.now(UTC).timestamp())

        return cls(
            ticker=ticker,
            price=price,
            timestamp=timestamp,
        )

    def to_dict(self) -> dict:
        """
        Convert PriceTick to dictionary.

        Returns:
            Dictionary representation of PriceTick.
        """
        if self.created_at:
            created_time = self.created_at.isoformat()
        else:
            created_time = None

        return {
            "id": self.id,
            "ticker": self.ticker,
            "price": self.price,
            "timestamp": self.timestamp,
            "created_at": created_time,
        }
