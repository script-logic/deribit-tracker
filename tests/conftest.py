"""
Pytest configuration and shared fixtures for Deribit Tracker tests.

Provides common test fixtures, configuration, and setup/teardown
functions for the entire test suite.
"""

import asyncio
from collections.abc import AsyncGenerator, Generator
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.main import app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """
    FastAPI TestClient fixture for HTTP endpoint testing.

    Yields:
        TestClient instance for making HTTP requests to the app.
    """
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def app_instance():
    """
    Raw FastAPI application instance.

    Returns:
        The FastAPI app instance for direct inspection or testing.
    """
    return app


@pytest.fixture(autouse=True)
def reset_settings():
    """
    Automatically reset Settings singleton before each test.

    Ensures clean state for settings-dependent tests.
    """
    original_instance = Settings._instance
    Settings._instance = None

    yield

    Settings._instance = original_instance


@pytest.fixture
def mock_settings():
    """
    Mock application settings for testing.

    Returns:
        Mock Settings instance with predefined values.
    """
    with patch("app.core.config.Settings.get_instance") as mock:
        mock_settings = Mock(spec=Settings)
        mock_settings.database.host = "test_host"
        mock_settings.database.port = 5432
        mock_settings.database.user = "test_user"
        mock_settings.database.password = Mock(
            get_secret_value=Mock(return_value="test_pass"),
        )
        mock_settings.database.db = "test_db"
        mock_settings.application.debug = False
        mock_settings.application.api_v1_prefix = "/api/v1"
        mock_settings.cors.origins = ["http://test.local"]
        mock.return_value = mock_settings

        yield mock_settings


@pytest.fixture
def mock_async_session():
    """
    Mock async database session for testing.

    Returns:
        Mock AsyncSession with common methods mocked.
    """
    session = AsyncMock(spec=AsyncSession)

    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    session.add = Mock()
    session.refresh = AsyncMock()

    return session


@pytest.fixture
def event_loop():
    """
    Create and manage asyncio event loop for async tests.

    Returns:
        AsyncIO event loop instance.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    yield loop

    loop.close()


@pytest.fixture(autouse=True)
def capture_logs(caplog):
    """
    Automatically capture logs for all tests.

    Args:
        caplog: Pytest's built-in caplog fixture.

    Returns:
        Configured caplog fixture.
    """
    caplog.set_level("DEBUG")

    return caplog


@pytest.fixture
def temp_env_file(tmp_path):
    """
    Create temporary .env file for environment variable testing.

    Args:
        tmp_path: Pytest temporary directory fixture.

    Returns:
        Path to temporary .env file.
    """
    env_file = tmp_path / ".env"
    env_content = """
DATABASE__HOST=test_host
DATABASE__PORT=5432
DATABASE__USER=test_user
DATABASE__PASSWORD=test_password
DATABASE__DB=test_db
APPLICATION__DEBUG=false
CORS__ORIGINS=["http://test.local"]
"""
    env_file.write_text(env_content)

    return env_file


def pytest_configure(config):
    """Register custom markers for test categorization."""
    config.addinivalue_line(
        "markers",
        "integration: mark test as integration test (requires "
        "external services)",
    )
    config.addinivalue_line(
        "markers",
        "slow: mark test as slow-running",
    )
    config.addinivalue_line(
        "markers",
        "async_test: mark test as requiring async execution",
    )


@pytest.fixture
def anyio_backend():
    """Configure anyio backend for async tests."""
    return "asyncio"


@pytest.fixture
async def async_client() -> AsyncGenerator[TestClient, None]:
    """
    Async-compatible TestClient fixture.

    Yields:
        TestClient instance for async HTTP testing.
    """
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def capture_all_output(capsys):
    """Capture all stdout/stderr output for tests."""
    yield
    capsys.readouterr()
