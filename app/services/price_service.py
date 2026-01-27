"""
Price service layer for business logic.

This service orchestrates between API layer and repository,
handling business rules, validation, and data transformation.
"""

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from app.core import get_logger
from app.database.models import PriceTick
from app.database.repository import PriceRepository

logger = get_logger(__name__)


class PriceService:
    """
    Service for price-related business operations.

    Provides high-level methods for API endpoints, handling
    business logic, validation, and error handling.
    """

    def __init__(self, repository: PriceRepository) -> None:
        """
        Initialize price service.

        Args:
            repository: PriceRepository instance.
        """
        self.repository = repository

    async def get_all_prices(
        self,
        ticker: str,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[PriceTick]:
        """
        Get all price records for a ticker with pagination.

        Args:
            ticker: Cryptocurrency ticker symbol.
            limit: Maximum number of records to return.
            offset: Number of records to skip.

        Returns:
            List of PriceTick records.

        Raises:
            ValueError: If ticker is not supported.
        """
        self._validate_ticker(ticker)
        logger.debug(
            "Getting prices for %s (limit: %s, offset: %s)",
            ticker,
            limit,
            offset,
        )

        return await self.repository.get_all_by_ticker(
            ticker=ticker,
            limit=limit,
            offset=offset,
        )

    async def get_latest_price(self, ticker: str) -> PriceTick | None:
        """
        Get latest price for a ticker.

        Args:
            ticker: Cryptocurrency ticker symbol.

        Returns:
            Latest PriceTick or None if not found.
        """
        self._validate_ticker(ticker)
        logger.debug("Getting latest price for %s", ticker)

        return await self.repository.get_latest_price(ticker)

    async def get_price_at_timestamp(
        self,
        ticker: str,
        timestamp: int,
    ) -> PriceTick | None:
        """
        Get price at exact timestamp.

        Args:
            ticker: Cryptocurrency ticker symbol.
            timestamp: UNIX timestamp.

        Returns:
            PriceTick at exact timestamp or None if not found.
        """
        self._validate_ticker(ticker)
        logger.debug(
            "Getting price for %s at timestamp %s",
            ticker,
            timestamp,
        )

        return await self.repository.get_price_at_timestamp(
            ticker=ticker,
            timestamp=timestamp,
        )

    async def get_price_closest_to_timestamp(
        self,
        ticker: str,
        timestamp: int,
        max_difference_seconds: int = 60,
    ) -> PriceTick | None:
        """
        Get price closest to target timestamp.

        Args:
            ticker: Cryptocurrency ticker symbol.
            timestamp: Target UNIX timestamp.
            max_difference_seconds: Maximum time difference in seconds.

        Returns:
            Closest PriceTick or None if not found.
        """
        self._validate_ticker(ticker)
        logger.debug(
            "Getting price closest to timestamp %s for %s (±%s seconds)",
            timestamp,
            ticker,
            max_difference_seconds,
        )

        return await self.repository.get_price_closest_to_timestamp(
            ticker=ticker,
            target_timestamp=timestamp,
            max_difference_seconds=max_difference_seconds,
        )

    async def get_prices_by_date_range(
        self,
        ticker: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
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
        self._validate_ticker(ticker)

        if start_date is None:
            start_date = datetime.now(UTC).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        if end_date is None:
            end_date = datetime.now(UTC)

        if start_date > end_date:
            start_date, end_date = end_date, start_date

        logger.debug(
            "Getting prices for %s from %s to %s",
            ticker,
            start_date,
            end_date,
        )

        return await self.repository.get_prices_by_date_range(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
        )

    async def get_price_statistics(
        self,
        ticker: str,
        target_timestamp: int | None = None,
    ) -> dict[str, Any]:
        """
        Get comprehensive price statistics.

        Args:
            ticker: Cryptocurrency ticker symbol.
            target_timestamp: Optional timestamp for specific price.

        Returns:
            Dictionary with price statistics.
        """
        self._validate_ticker(ticker)

        latest_price = await self.repository.get_latest_price(ticker)
        all_prices = await self.repository.get_all_by_ticker(ticker)

        price_at_time = None
        closest_price = None

        if target_timestamp is not None:
            price_at_time_tick = await self.repository.get_price_at_timestamp(
                ticker=ticker,
                timestamp=target_timestamp,
            )
            if price_at_time_tick:
                price_at_time = price_at_time_tick.price

            closest_price_tick = (
                await self.repository.get_price_closest_to_timestamp(
                    ticker=ticker,
                    target_timestamp=target_timestamp,
                )
            )
            if closest_price_tick:
                closest_price = closest_price_tick.price

        prices = [tick.price for tick in all_prices]

        if not prices:
            return {
                "ticker": ticker,
                "latest_price": None,
                "latest_timestamp": None,
                "count": 0,
                "price_at_time": None,
                "closest_price": None,
                "min_price": None,
                "max_price": None,
                "avg_price": None,
            }

        return {
            "ticker": ticker,
            "latest_price": latest_price.price if latest_price else None,
            "latest_timestamp": (
                latest_price.timestamp if latest_price else None
            ),
            "count": len(prices),
            "price_at_time": price_at_time,
            "closest_price": closest_price,
            "min_price": min(prices) if prices else None,
            "max_price": max(prices) if prices else None,
            "avg_price": (sum(prices) / len(prices) if prices else None),
        }

    async def create_price_tick(
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

        Raises:
            ValueError: If price is negative.
        """
        self._validate_ticker(ticker)

        if price < 0:
            raise ValueError(f"Price cannot be negative: {price}")

        logger.debug("Creating price tick for %s: %s", ticker, price)

        return await self.repository.create(
            ticker=ticker,
            price=price,
            timestamp=timestamp,
        )

    @staticmethod
    def _validate_ticker(ticker: str) -> None:
        """
        Validate ticker symbol.

        Args:
            ticker: Ticker to validate.

        Raises:
            ValueError: If ticker is not supported.
        """
        normalized_ticker = ticker.strip().lower()
        if normalized_ticker not in {"btc_usd", "eth_usd"}:
            raise ValueError(
                f"Unsupported ticker: {ticker}. "
                f"Supported: 'btc_usd', 'eth_usd'"
            )
