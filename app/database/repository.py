from collections.abc import AsyncGenerator, Sequence
from contextlib import asynccontextmanager
from datetime import datetime

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from . import database_manager
from .models import PriceTick


@asynccontextmanager
async def get_repository_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for repository operations.
    Uses existed DatabaseManager.
    """
    async with database_manager.get_session() as session:
        yield session


class PriceRepository:
    """
    Repository for PriceTick database operations.

    Implements data access layer with business logic separation.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async session.
        """
        self.session = session

    async def create(
        self,
        ticker: str,
        price: float,
        timestamp: int | None = None,
    ) -> PriceTick:
        """
        Create new price tick record.

        Args:
            ticker: Cryptocurrency ticker symbol.
            price: Current price in USD.
            timestamp: UNIX timestamp (defaults to current time).

        Returns:
            Created PriceTick instance.
        """
        price_tick = PriceTick.create(
            ticker=ticker,
            price=price,
            timestamp=timestamp,
        )
        self.session.add(price_tick)
        await self.session.flush()
        await self.session.refresh(price_tick)
        return price_tick

    async def get_all_by_ticker(
        self,
        ticker: str,
        limit: int | None = None,
        offset: int = 0,
    ) -> Sequence[PriceTick]:
        """
        Get all price records for specific ticker.

        Args:
            ticker: Cryptocurrency ticker symbol.
            limit: Maximum number of records to return.
            offset: Number of records to skip.

        Returns:
            List of PriceTick records.
        """
        query = (
            select(PriceTick)
            .where(PriceTick.ticker == ticker)
            .order_by(desc(PriceTick.timestamp))
            .offset(offset)
        )

        if limit is not None:
            query = query.limit(limit)

        result = await self.session.execute(query)

        ticks: Sequence[PriceTick] = result.scalars().all()
        return ticks

    async def get_latest_price(self, ticker: str) -> PriceTick | None:
        """
        Get latest price for specific ticker.

        Args:
            ticker: Cryptocurrency ticker symbol.

        Returns:
            Latest PriceTick record or None if not found.
        """
        query = (
            select(PriceTick)
            .where(PriceTick.ticker == ticker)
            .order_by(desc(PriceTick.timestamp))
            .limit(1)
        )

        result = await self.session.execute(query)

        tick: PriceTick | None = result.scalar_one_or_none()
        return tick

    async def get_price_at_timestamp(
        self,
        ticker: str,
        timestamp: int,
    ) -> PriceTick | None:
        """
        Get price for specific ticker at exact timestamp.

        Args:
            ticker: Cryptocurrency ticker symbol.
            timestamp: UNIX timestamp to search for.

        Returns:
            PriceTick record at exact timestamp or None if not found.
        """
        query = select(PriceTick).where(
            PriceTick.ticker == ticker,
            PriceTick.timestamp == timestamp,
        )

        result = await self.session.execute(query)

        tick: PriceTick | None = result.scalar_one_or_none()
        return tick

    async def get_price_closest_to_timestamp(
        self,
        ticker: str,
        target_timestamp: int,
        max_difference_seconds: int = 60,
    ) -> PriceTick | None:
        """
        Get price closest to target timestamp within time window.

        Args:
            ticker: Cryptocurrency ticker symbol.
            target_timestamp: Target UNIX timestamp.
            max_difference_seconds: Maximum time difference in seconds.

        Returns:
            Closest PriceTick record or None if not found within window.
        """
        min_timestamp = target_timestamp - max_difference_seconds
        max_timestamp = target_timestamp + max_difference_seconds

        query = (
            select(PriceTick)
            .where(
                PriceTick.ticker == ticker,
                PriceTick.timestamp >= min_timestamp,
                PriceTick.timestamp <= max_timestamp,
            )
            .order_by(
                func.abs(PriceTick.timestamp - target_timestamp),
            )
            .limit(1)
        )

        result = await self.session.execute(query)

        tick: PriceTick | None = result.scalar_one_or_none()
        return tick

    async def get_prices_by_date_range(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
    ) -> Sequence[PriceTick]:
        """
        Get prices within date range.

        Args:
            ticker: Cryptocurrency ticker symbol.
            start_date: Start datetime (inclusive).
            end_date: End datetime (inclusive).

        Returns:
            List of PriceTick records within date range.
        """
        start_timestamp = int(start_date.timestamp())
        end_timestamp = int(end_date.timestamp())

        query = (
            select(PriceTick)
            .where(
                PriceTick.ticker == ticker,
                PriceTick.timestamp >= start_timestamp,
                PriceTick.timestamp <= end_timestamp,
            )
            .order_by(PriceTick.timestamp)
        )

        result = await self.session.execute(query)

        ticks: Sequence[PriceTick] = result.scalars().all()
        return ticks
