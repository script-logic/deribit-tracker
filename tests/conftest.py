from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import Settings
from app.database import DatabaseManager


@pytest.fixture(scope="session")
def mock_settings() -> Settings:
    """Mock application settings."""
    return Settings.init_instance()


@pytest.fixture
def mock_db_session() -> MagicMock:
    """Mock SQLAlchemy AsyncSession."""
    session = MagicMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def mock_db_manager(mock_db_session: MagicMock) -> MagicMock:
    """Mock DatabaseManager."""
    manager = MagicMock(spec=DatabaseManager)
    manager.get_session = MagicMock()
    manager.get_session.return_value.__aenter__.return_value = mock_db_session
    return manager
