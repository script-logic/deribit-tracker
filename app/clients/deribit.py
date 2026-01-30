"""
Deribit API client for cryptocurrency price data.

Provides async methods to fetch index prices for BTC and ETH
using Deribit's public API endpoints.
"""

import asyncio
from typing import Any

import aiohttp
from aiohttp import ClientError, ClientResponseError, ClientTimeout

from app.core import get_logger

from .exceptions import DeribitAPIError


class DeribitClient:
    """
    Async client for Deribit API with connection pooling and error
    handling.

    Uses aiohttp for efficient async HTTP requests with configurable
    timeouts and retry logic for public endpoints.
    """

    _session: aiohttp.ClientSession | None = None
    _timeout = ClientTimeout(total=30, connect=10)

    def __init__(
        self,
        base_url: str,
    ) -> None:
        """
        Initialize Deribit client.

        Args:
            logger: Logger instance.
            base_url: Deribit API base URL. Defaults to settings.
        """
        self.logger = get_logger()
        self.base_url = base_url
        self._headers = {"Content-Type": "application/json"}

    @classmethod
    async def get_session(cls) -> aiohttp.ClientSession:
        """
        Get or create shared aiohttp session with connection pooling.

        Returns:
            Reusable aiohttp ClientSession instance.
        """
        if cls._session is None or cls._session.closed:
            connector = aiohttp.TCPConnector(
                limit=20,
                limit_per_host=5,
                ttl_dns_cache=300,
                force_close=False,
                enable_cleanup_closed=True,
            )
            cls._session = aiohttp.ClientSession(
                connector=connector,
                timeout=cls._timeout,
                headers={"Content-Type": "application/json"},
            )
        return cls._session

    @classmethod
    async def close_session(cls) -> None:
        """Close shared aiohttp session."""
        if cls._session and not cls._session.closed:
            await cls._session.close()
            cls._session = None

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        max_retries: int = 3,
    ) -> dict[str, Any]:
        """
        Make HTTP request to Deribit API with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Query parameters
            max_retries: Maximum number of retry attempts

        Returns:
            JSON response data

        Raises:
            DeribitAPIError: If request fails after all retries
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        session = await self.get_session()

        for attempt in range(max_retries):
            try:
                async with session.request(
                    method=method,
                    url=url,
                    params=params,
                    headers=self._headers,
                ) as response:
                    response.raise_for_status()
                    data: dict[str, Any] = await response.json()

                    if data.get("error"):
                        error_msg = data["error"].get(
                            "message",
                            "Unknown error",
                        )
                        raise DeribitAPIError(
                            f"API error: {error_msg}",
                            status_code=response.status,
                        )

                    return data

            except ClientResponseError as error:
                if error.status >= 500 and attempt < max_retries - 1:
                    wait_time = 2**attempt
                    self.logger.warning(
                        "Server error %s, retrying in %s seconds...",
                        error.status,
                        wait_time,
                    )
                    await asyncio.sleep(wait_time)
                    continue

                raise DeribitAPIError(
                    f"HTTP error {error.status}: {error.message}",
                    status_code=error.status,
                ) from error

            except ClientError as error:
                if attempt < max_retries - 1:
                    wait_time = 2**attempt
                    self.logger.warning(
                        "Connection error: %s, retrying in %s seconds...",
                        error,
                        wait_time,
                    )
                    await asyncio.sleep(wait_time)
                    continue

                raise DeribitAPIError(
                    f"Network error: {error!s}",
                ) from error

            except TimeoutError as error:
                if attempt < max_retries - 1:
                    wait_time = 2**attempt
                    self.logger.warning(
                        "Timeout, retrying in %s seconds...",
                        wait_time,
                    )
                    await asyncio.sleep(wait_time)
                    continue

                raise DeribitAPIError("Request timeout") from error

        raise DeribitAPIError("Max retries exceeded")

    async def get_index_price(self, currency: str) -> float:
        """
        Get current index price for specified currency.

        Args:
            currency: Currency pair (e.g., 'btc_usd', 'eth_usd')

        Returns:
            Current index price as float

        Raises:
            DeribitAPIError: If price cannot be retrieved
            ValueError: If currency format is invalid
        """
        if currency.lower() not in {"btc_usd", "eth_usd"}:
            raise ValueError(
                f"Unsupported currency: {currency}. "
                "Supported: 'btc_usd', 'eth_usd'",
            )

        try:
            response = await self._make_request(
                method="GET",
                endpoint="/public/get_index_price",
                params={"index_name": currency},
            )

            if "result" not in response:
                raise DeribitAPIError(
                    "Invalid response format: missing 'result'",
                )

            result = response["result"]

            if "index_price" not in result:
                raise DeribitAPIError(
                    "Invalid response format: missing 'index_price'",
                )

            price = float(result["index_price"])
            self.logger.debug("Retrieved %s price: %s", currency, price)
            return price

        except (KeyError, ValueError, TypeError) as error:
            raise DeribitAPIError(
                f"Failed to parse price data: {error!s}",
            ) from error

    async def get_btc_price(self) -> float:
        """Get current BTC index price."""
        return await self.get_index_price("btc_usd")

    async def get_eth_price(self) -> float:
        """Get current ETH index price."""
        return await self.get_index_price("eth_usd")

    async def get_all_prices(self) -> dict[str, float]:
        """
        Get current prices for all supported currencies.

        Returns:
            Dictionary with ticker-price pairs
        """
        currencies = ["btc_usd", "eth_usd"]
        tasks = [self.get_index_price(currency) for currency in currencies]

        try:
            prices = await asyncio.gather(*tasks, return_exceptions=True)

            result: dict[str, float] = {}
            for currency, price in zip(currencies, prices, strict=False):
                if isinstance(price, BaseException):
                    self.logger.error(
                        "Failed to get %s price: %s", currency, price
                    )
                    continue

                result[currency] = price

            return result

        except Exception as error:
            self.logger.error("Failed to get prices: %s", error)
            raise

    async def health_check(self) -> bool:
        """
        Check if Deribit API is accessible.

        Returns:
            True if API is responsive
        """
        try:
            await self._make_request("GET", "/public/test", max_retries=1)
            return True
        except DeribitAPIError:
            return False
