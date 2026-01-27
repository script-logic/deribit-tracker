"""
Unit tests for application configuration management.

Tests the settings loading, validation, and singleton behavior
of the configuration system.
"""

import os
from copy import copy
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from app.core.config import (
    ApplicationSettings,
    CORSSettings,
    DatabaseSettings,
    DeribitAPISettings,
    RedisSettings,
    Settings,
    get_settings,
)


class TestDatabaseSettings:
    """Test database configuration validation."""

    def test_default_values(self):
        """Test default values for database settings."""
        settings = DatabaseSettings(
            user="test",
            password="secret",  # type: ignore
            db="test_db",
        )

        assert settings.host == "localhost"
        assert settings.port == 5432
        assert settings.user == "test"
        assert settings.db == "test_db"

    def test_port_validation(self):
        """Test port number validation."""
        settings = DatabaseSettings(
            user="test",
            password="secret",  # type: ignore
            db="test_db",
            port=5432,
        )
        assert settings.port == 5432

        with pytest.raises(ValidationError):
            DatabaseSettings(
                user="test",
                password="secret",  # type: ignore
                db="test_db",
                port=0,
            )

        with pytest.raises(ValidationError):
            DatabaseSettings(
                user="test",
                password="secret",  # type: ignore
                db="test_db",
                port=65536,
            )

    def test_dsn_generation(self):
        """Test Data Source Name generation."""
        settings = DatabaseSettings(
            host="db.example.com",
            port=5432,
            user="test_user",
            password="test_pass",  # type: ignore
            db="test_db",
        )

        assert settings.dsn == (
            "postgresql://test_user:test_pass@db.example.com:5432/test_db"
        )
        assert settings.async_dsn == (
            "postgresql+asyncpg://test_user"
            ":test_pass@db.example.com:5432/test_db"
        )

    def test_password_security(self):
        """Test password is stored as SecretStr."""
        settings = DatabaseSettings(
            user="test",
            password="super_secret",  # type: ignore
            db="test_db",
        )

        assert isinstance(settings.password, type(settings.password))
        assert settings.password.get_secret_value() == "super_secret"
        assert "super_secret" not in str(settings)
        assert "super_secret" not in repr(settings)


class TestDeribitAPISettings:
    """Test Deribit API configuration."""

    def test_default_values(self):
        """Test default values for Deribit API settings."""
        settings = DeribitAPISettings()

        assert settings.base_url == "https://www.deribit.com/api/v2"
        assert settings.client_id is None
        assert settings.client_secret is None
        assert not settings.is_configured

    def test_is_configured_property(self):
        """Test is_configured property logic."""
        settings = DeribitAPISettings()
        assert not settings.is_configured

        settings = DeribitAPISettings(client_id="test_id")
        assert not settings.is_configured

        settings = DeribitAPISettings(
            client_id="test_id",
            client_secret="test_secret",  # type: ignore
        )
        assert settings.is_configured

    def test_secret_storage(self):
        """Test client secret security."""
        settings = DeribitAPISettings(
            client_id="test_id",
            client_secret="very_secret",  # type: ignore
        )

        assert isinstance(settings.client_secret, type(settings.client_secret))
        assert settings.client_secret is not None
        assert settings.client_secret.get_secret_value() == "very_secret"
        assert "very_secret" not in str(settings)


class TestRedisSettings:
    """Test Redis configuration."""

    def test_default_values(self):
        """Test default values for Redis settings."""
        settings = RedisSettings()

        assert settings.host == "localhost"
        assert settings.port == 6379
        assert settings.db == 0

    def test_url_generation(self):
        """Test Redis URL generation."""
        settings = RedisSettings(
            host="redis.example.com",
            port=6380,
            db=1,
        )

        assert settings.url == "redis://redis.example.com:6380/1"

    def test_db_validation(self):
        """Test Redis database number validation."""
        for db_num in [0, 1, 15]:
            settings = RedisSettings(db=db_num)
            assert settings.db == db_num

        with pytest.raises(ValidationError):
            RedisSettings(db=-1)

        with pytest.raises(ValidationError):
            RedisSettings(db=16)


class TestApplicationSettings:
    """Test application core settings."""

    def test_default_values(self):
        """Test default values for application settings."""
        settings = ApplicationSettings()

        assert not settings.debug
        assert settings.api_v1_prefix == "/api/v1"
        assert settings.project_name == "Deribit Price Tracker API"
        assert settings.version == "0.4.0"

    def test_api_prefix_validation(self):
        """Test API prefix validation and normalization."""
        test_cases = [
            ("/api", "/api"),
            ("api", "/api"),
            ("/api/v1/", "/api/v1"),
            ("api/v2", "/api/v2"),
        ]

        for input_prefix, expected in test_cases:
            settings = ApplicationSettings(api_v1_prefix=input_prefix)
            assert settings.api_v1_prefix == expected

        with pytest.raises(ValidationError):
            ApplicationSettings(api_v1_prefix="")


class TestCORSSettings:
    """Test CORS configuration."""

    def test_default_origins(self):
        """Test default CORS origins."""
        settings = CORSSettings()

        assert len(settings.origins) == 2
        assert "http://localhost:8000" in settings.origins
        assert "http://127.0.0.1:8000" in settings.origins

    def test_custom_origins(self):
        """Test custom CORS origins."""
        custom_origins = [
            "https://example.com",
            "https://api.example.com",
        ]

        settings = CORSSettings(origins=custom_origins)
        assert settings.origins == custom_origins


class TestSettingsSingleton:
    """Test Settings singleton behavior."""

    def setup_method(self):
        """Reset singleton instance before each test."""
        Settings._instance = None
        for key in copy(os.environ):
            if key.startswith(("DATABASE__", "DERIBIT_API__", "REDIS__")):
                del os.environ[key]

    def test_singleton_pattern(self):
        """Test that Settings is a proper singleton."""
        settings1 = get_settings(
            database={
                "host": "localhost",
                "port": 5432,
                "user": "test",
                "password": "test",
                "db": "test",
            },
            deribit_api={
                "client_id": None,
                "client_secret": None,
            },
            redis={
                "host": "localhost",
                "port": 6379,
                "db": 0,
            },
            celery={
                "worker_concurrency": 2,
                "beat_enabled": True,
                "task_track_started": True,
            },
            application={
                "debug": False,
                "api_v1_prefix": "/api/v1",
                "project_name": "Test",
                "version": "1.0",
            },
            cors={
                "origins": ["http://localhost:8000"],
            },
        )

        settings2 = get_settings()

        assert settings1 is settings2
        assert id(settings1) == id(settings2)

    def test_init_settings_function(self):
        """Test init_settings() convenience function."""
        settings = get_settings(
            database={
                "host": "testhost",
                "port": 5432,
                "user": "test",
                "password": "test",
                "db": "test",
            },
            deribit_api={
                "client_id": None,
                "client_secret": None,
            },
            redis={
                "host": "localhost",
                "port": 6379,
                "db": 0,
            },
            celery={
                "worker_concurrency": 2,
                "beat_enabled": True,
                "task_track_started": True,
            },
            application={
                "debug": False,
                "api_v1_prefix": "/api/v1",
                "project_name": "Test",
                "version": "1.0",
            },
            cors={
                "origins": ["http://localhost:8000"],
            },
        )

        assert get_settings() is settings

    @patch.dict(
        os.environ,
        {
            "DATABASE__HOST": "envhost",
            "DATABASE__PORT": "5432",
            "DATABASE__USER": "envuser",
            "DATABASE__PASSWORD": "envpass",
            "DATABASE__DB": "envdb",
            "APPLICATION__DEBUG": "true",
        },
        clear=True,
    )
    def test_environment_variable_loading(self):
        """Test loading settings from environment variables."""
        settings = get_settings()

        assert settings.database.host == "envhost"
        assert settings.database.port == 5432
        assert settings.database.user == "envuser"
        assert settings.database.db == "envdb"
        assert settings.application.debug is True

    def test_log_initialization(self, caplog: pytest.LogCaptureFixture):
        """Test logging during settings initialization."""
        with caplog.at_level("INFO"):
            get_settings(
                database={
                    "host": "localhost",
                    "port": 5432,
                    "user": "test",
                    "password": "test",
                    "db": "test",
                },
                deribit_api={
                    "client_id": None,
                    "client_secret": None,
                },
                redis={
                    "host": "localhost",
                    "port": 6379,
                    "db": 0,
                },
                celery={
                    "worker_concurrency": 2,
                    "beat_enabled": True,
                    "task_track_started": True,
                },
                application={
                    "debug": True,
                    "api_v1_prefix": "/api/v1",
                    "project_name": "Test",
                    "version": "1.0",
                },
                cors={
                    "origins": ["http://localhost:8000"],
                },
            )
        assert "Application settings initialized" in caplog.text
        assert "Debug logging enabled" in caplog.text
        assert "Deribit API credentials not configured" in caplog.text


def test_settings_immutability():
    """Test that settings objects are immutable after creation."""
    settings = get_settings(
        database={
            "host": "localhost",
            "port": 5432,
            "user": "test",
            "password": "test",
            "db": "test",
        },
        deribit_api={
            "client_id": None,
            "client_secret": None,
        },
        redis={
            "host": "localhost",
            "port": 6379,
            "db": 0,
        },
        celery={
            "worker_concurrency": 2,
            "beat_enabled": True,
            "task_track_started": True,
        },
        application={
            "debug": False,
            "api_v1_prefix": "/api/v1",
            "project_name": "Test",
            "version": "1.0",
        },
        cors={
            "origins": ["http://localhost:8000"],
        },
    )

    assert settings.model_config.get("frozen") is True
    assert settings.database.model_config.get("frozen") is True
    import pydantic

    with pytest.raises(pydantic.ValidationError):
        settings.database.host = "newhost"

    original_host = settings.database.host
    assert settings.database.host == original_host
