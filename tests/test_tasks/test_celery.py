from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.tasks.price_collection import collect_single_price


@pytest.mark.unit
class TestCeleryTasks:
    @pytest.mark.asyncio
    @patch("app.tasks.price_collection.get_deribit_client_tasks")
    @patch("app.tasks.price_collection.get_database_manager_tasks")
    async def test_collect_single_price_success(
        self,
        mock_get_db_manager: MagicMock,
        mock_get_client: MagicMock,
    ) -> None:
        """Test successful execution of collection task."""
        mock_client = AsyncMock()
        mock_client.get_index_price.return_value = 50000.0
        mock_get_client.return_value = mock_client

        mock_db_session = AsyncMock()
        mock_db_manager = MagicMock()
        mock_db_manager.get_session.return_value.__aenter__.return_value = (
            mock_db_session
        )
        mock_get_db_manager.return_value = mock_db_manager

        with patch("app.tasks.price_collection.PriceRepository") as MockRepo:
            mock_repo_instance = MagicMock()
            mock_repo_instance.create = AsyncMock()
            mock_repo_instance.create.return_value.id = 123
            MockRepo.return_value = mock_repo_instance

            result = await collect_single_price("btc_usd")

        assert result is not None
        assert result["success"] is True
        assert result["price"] == 50000.0
        assert result["record_id"] == 123

    @pytest.mark.asyncio
    async def test_collect_single_price_invalid_ticker(self) -> None:
        """Test task behavior with unsupported ticker."""
        result = await collect_single_price("invalid")
        assert result is None
