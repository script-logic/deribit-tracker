from unittest.mock import AsyncMock, MagicMock

import pytest

from app.database import PriceRepository
from app.database.models import PriceTick
from app.services import PriceService


@pytest.mark.unit
class TestPriceService:
    @pytest.fixture
    def mock_repo(self) -> MagicMock:
        return MagicMock(spec=PriceRepository)

    @pytest.fixture
    def service(self, mock_repo: MagicMock) -> PriceService:
        return PriceService(mock_repo)

    @pytest.mark.asyncio
    async def test_get_latest_price_success(
        self,
        service: PriceService,
        mock_repo: MagicMock,
    ) -> None:
        """Test successful retrieval of latest price."""
        expected_tick = PriceTick(ticker="btc_usd", price=100.0)
        mock_repo.get_latest_price = AsyncMock(return_value=expected_tick)

        result = await service.get_latest_price("btc_usd")

        assert result == expected_tick
        mock_repo.get_latest_price.assert_called_once_with("btc_usd")

    @pytest.mark.asyncio
    async def test_validate_ticker_invalid(
        self,
        service: PriceService,
    ) -> None:
        """Test validation raises error for unsupported ticker."""
        with pytest.raises(ValueError, match="Unsupported ticker"):
            await service.get_latest_price("invalid_pair")

    @pytest.mark.asyncio
    async def test_create_price_tick_negative_price(
        self,
        service: PriceService,
    ) -> None:
        """Test validation raises error for negative price."""
        with pytest.raises(ValueError, match="Price cannot be negative"):
            await service.create_price_tick("btc_usd", -500.0)

    @pytest.mark.asyncio
    async def test_get_price_statistics_empty(
        self,
        service: PriceService,
        mock_repo: MagicMock,
    ) -> None:
        """Test statistics calculation when no data exists."""
        mock_repo.get_latest_price = AsyncMock(return_value=None)
        mock_repo.get_all_by_ticker = AsyncMock(return_value=[])
        mock_repo.get_price_at_timestamp = AsyncMock(return_value=None)
        mock_repo.get_price_closest_to_timestamp = AsyncMock(return_value=None)

        stats = await service.get_price_statistics("btc_usd")

        assert stats["count"] == 0
        assert stats["min_price"] is None
        assert stats["avg_price"] is None

    @pytest.mark.asyncio
    async def test_get_price_statistics_calculated(
        self,
        service: PriceService,
        mock_repo: MagicMock,
    ) -> None:
        """Test statistics calculation with data."""
        ticks = [
            PriceTick(price=100.0),
            PriceTick(price=200.0),
            PriceTick(price=300.0),
        ]
        mock_repo.get_latest_price = AsyncMock(return_value=ticks[-1])
        mock_repo.get_all_by_ticker = AsyncMock(return_value=ticks)
        mock_repo.get_price_at_timestamp = AsyncMock(return_value=None)
        mock_repo.get_price_closest_to_timestamp = AsyncMock(return_value=None)

        stats = await service.get_price_statistics("btc_usd")

        assert stats["count"] == 3
        assert stats["min_price"] == 100.0
        assert stats["max_price"] == 300.0
        assert stats["avg_price"] == 200.0
