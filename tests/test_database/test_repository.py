import time
from unittest.mock import MagicMock

import pytest

from app.database import PriceRepository
from app.database.models import PriceTick


@pytest.mark.unit
class TestPriceRepository:
    @pytest.fixture
    def repository(self, mock_db_session: MagicMock) -> PriceRepository:
        return PriceRepository(mock_db_session)

    @pytest.mark.asyncio
    async def test_create_price_tick(
        self,
        repository: PriceRepository,
        mock_db_session: MagicMock,
    ) -> None:
        """Test creating a new price tick record."""
        ticker = "btc_usd"
        price = 50000.0
        timestamp = int(time.time())

        result = await repository.create(ticker, price, timestamp)

        assert isinstance(result, PriceTick)
        assert result.ticker == ticker
        assert result.price == price
        assert result.timestamp == timestamp
        mock_db_session.add.assert_called_once()
        mock_db_session.flush.assert_called_once()
        mock_db_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all_by_ticker(
        self,
        repository: PriceRepository,
        mock_db_session: MagicMock,
    ) -> None:
        """Test retrieving all records for a ticker."""
        mock_result = MagicMock()

        expected_ticks = [
            PriceTick(ticker="btc_usd", price=50000.0, id=1),
            PriceTick(ticker="btc_usd", price=51000.0, id=2),
        ]
        mock_result.scalars.return_value.all.return_value = expected_ticks

        mock_db_session.execute.return_value = mock_result

        result = await repository.get_all_by_ticker("btc_usd", limit=10)

        assert len(result) == 2
        mock_db_session.execute.assert_called_once()
        mock_result.scalars.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_latest_price(
        self,
        repository: PriceRepository,
        mock_db_session: MagicMock,
    ) -> None:
        """Test retrieving the latest price."""
        expected_tick = PriceTick(ticker="btc_usd", price=55000.0, id=1)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = expected_tick

        mock_db_session.execute.return_value = mock_result

        result = await repository.get_latest_price("btc_usd")

        assert result == expected_tick
        mock_db_session.execute.assert_called_once()
        mock_result.scalar_one_or_none.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_price_closest_to_timestamp(
        self,
        repository: PriceRepository,
        mock_db_session: MagicMock,
    ) -> None:
        """Test retrieving price within time window."""
        expected_tick = PriceTick(
            ticker="btc_usd",
            price=50000.0,
            timestamp=1000,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = expected_tick

        mock_db_session.execute.return_value = mock_result

        result = await repository.get_price_closest_to_timestamp(
            "btc_usd",
            1005,
            60,
        )

        assert result == expected_tick
        mock_db_session.execute.assert_called_once()
