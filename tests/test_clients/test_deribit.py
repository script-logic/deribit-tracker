from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from app.clients import DeribitClient
from app.clients.exceptions import DeribitAPIError


@pytest.mark.unit
class TestDeribitClient:
    @pytest.fixture
    def client(self) -> DeribitClient:
        return DeribitClient(base_url="https://test.deribit.com")

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.request")
    async def test_get_index_price_success(
        self,
        mock_request: MagicMock,
        client: DeribitClient,
    ) -> None:
        """Test successful price retrieval."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "result": {"index_price": 50000.0},
        }
        mock_request.return_value.__aenter__.return_value = mock_response

        with patch.object(
            client,
            "get_session",
            new_callable=AsyncMock,
        ) as mock_get_session:
            mock_session = MagicMock()
            mock_session.request = mock_request
            mock_get_session.return_value = mock_session

            price = await client.get_index_price("btc_usd")

        assert price == 50000.0
        mock_response.raise_for_status.assert_called_once()
        mock_response.json.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_index_price_invalid_currency(
        self,
        client: DeribitClient,
    ) -> None:
        """Test invalid currency raises ValueError."""
        with pytest.raises(ValueError):
            await client.get_index_price("invalid")

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.request")
    async def test_api_server_error_retry(
        self,
        mock_request: MagicMock,
        client: DeribitClient,
    ) -> None:
        """
        Test that 500 errors trigger retries and raise specific exception.
        """
        req_info = MagicMock()
        history = MagicMock()

        mock_request.side_effect = aiohttp.ClientResponseError(
            request_info=req_info,
            history=history,
            status=500,
            message="Server Error",
        )

        with patch.object(
            client,
            "get_session",
            new_callable=AsyncMock,
        ) as mock_get_session:
            mock_session = MagicMock()
            mock_session.request = mock_request
            mock_get_session.return_value = mock_session
            alias_private = (
                client._make_request  # pyright: ignore[reportPrivateUsage]
            )
            with patch("asyncio.sleep", new_callable=AsyncMock):
                with pytest.raises(DeribitAPIError) as exc:
                    await alias_private("GET", "/test", max_retries=2)

        assert "HTTP error 500" in str(exc.value)

    @pytest.mark.asyncio
    @patch("app.clients.DeribitClient.get_index_price")
    async def test_get_all_prices(
        self,
        mock_get_price: AsyncMock,
        client: DeribitClient,
    ) -> None:
        """Test gathering multiple prices."""

        async def side_effect(currency: str) -> float:  # noqa: RUF029
            if currency == "btc_usd":
                return 50000.0
            return 3000.0

        mock_get_price.side_effect = side_effect

        result = await client.get_all_prices()

        assert result["btc_usd"] == 50000.0
        assert result["eth_usd"] == 3000.0
        assert len(result) == 2
