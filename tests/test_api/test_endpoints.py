from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.database.models import PriceTick
from app.dependencies.database import get_db_session
from app.dependencies.services import get_price_service
from app.main import app
from app.services import PriceService


@pytest.mark.unit
class TestAPIEndpoints:
    @pytest.fixture
    def mock_service(self) -> AsyncMock:
        return AsyncMock(spec_set=PriceService)

    @pytest.fixture
    async def client(
        self,
        mock_service: AsyncMock,
    ) -> AsyncGenerator[Any, None]:
        """
        Create test client with overridden dependencies.
        """
        app.dependency_overrides[get_price_service] = lambda: mock_service
        app.dependency_overrides[get_db_session] = lambda: AsyncMock()

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test/api/v1",
        ) as ac:
            yield ac

        app.dependency_overrides = {}

    @pytest.mark.asyncio
    async def test_get_latest_price_success(
        self,
        client: AsyncClient,
        mock_service: AsyncMock,
    ) -> None:
        """Test getting latest price endpoint."""
        expected_tick = PriceTick(
            id=1,
            ticker="btc_usd",
            price=50000.0,
            timestamp=1700000000,
            created_at=datetime.now(UTC),
        )
        mock_service.get_latest_price.return_value = expected_tick

        response = await client.get("/prices/latest?ticker=btc_usd")

        assert response.status_code == 200
        data = response.json()
        assert data["price"] == 50000.0
        assert data["ticker"] == "btc_usd"
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_get_latest_price_not_found(
        self,
        client: AsyncClient,
        mock_service: AsyncMock,
    ) -> None:
        """Test 404 response when no price found."""
        mock_service.get_latest_price.return_value = None

        response = await client.get("/prices/latest?ticker=btc_usd")

        assert response.status_code == 404
        assert response.json()["error_type"] == "not_found"

    @pytest.mark.asyncio
    async def test_get_all_prices_pagination(
        self,
        client: AsyncClient,
        mock_service: AsyncMock,
    ) -> None:
        """Test pagination parameters passing."""
        mock_service.get_all_prices.return_value = []

        await client.get("/prices/?ticker=btc_usd&limit=50&offset=10")

        mock_service.get_all_prices.assert_awaited_once_with(
            ticker="btc_usd",
            limit=50,
            offset=10,
        )

    @pytest.mark.asyncio
    async def test_get_stats_empty(
        self,
        client: AsyncClient,
        mock_service: AsyncMock,
    ) -> None:
        """Test stats endpoint handles empty data correctly."""
        mock_service.get_price_statistics.return_value = {
            "ticker": "btc_usd",
            "count": 0,
            "min_price": None,
            "max_price": None,
            "avg_price": None,
            "latest_price": None,
            "latest_timestamp": None,
            "price_at_time": None,
            "closest_price": None,
        }

        response = await client.get("/prices/stats?ticker=btc_usd")

        assert response.status_code == 404
        assert response.json()["error_type"] == "not_found"
