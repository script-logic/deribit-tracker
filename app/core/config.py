"""
Application configuration management with environment-based settings.

Uses Pydantic for type-safe configuration with support for nested models,
environment variable loading, and singleton pattern for global access.
"""

from typing import Any, ClassVar

from pydantic import BaseModel, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .logger import AppLogger, get_logger


class DatabaseSettings(BaseModel):
    """
    PostgreSQL database configuration.

    Attributes:
        host: Database server hostname.
        port: Database server port (1-65535).
        user: Database authentication username.
        password: Database authentication password (secured).
        db: Database name.
    """

    host: str = "localhost"
    port: int = Field(default=5432, ge=1, le=65535)
    user: str
    password: SecretStr
    db: str

    model_config = {"frozen": True}

    @property
    def dsn(self) -> str:
        """
        Data Source Name for PostgreSQL connection.

        Returns:
            PostgreSQL connection string in format:
            postgresql://user:password@host:port/db
        """
        return (
            f"postgresql://{self.user}:{self.password.get_secret_value()}"
            f"@{self.host}:{self.port}/{self.db}"
        )

    @property
    def async_dsn(self) -> str:
        """
        Async Data Source Name for SQLAlchemy with asyncpg.

        Returns:
            Async PostgreSQL connection string in format:
            postgresql+asyncpg://user:password@host:port/db
        """
        return (
            f"postgresql+asyncpg://{self.user}"
            f":{self.password.get_secret_value()}"
            f"@{self.host}:{self.port}/{self.db}"
        )


class DeribitAPISettings(BaseModel):
    """
    Deribit API client configuration.

    Attributes:
        client_id: Deribit API client identifier.
        client_secret: Deribit API client secret (secured).
        base_url: Deribit API base endpoint URL.
    """

    client_id: str | None = None
    client_secret: SecretStr | None = None
    base_url: str = "https://www.deribit.com/api/v2"

    model_config = {"frozen": True}

    @property
    def is_configured(self) -> bool:
        """
        Check if API credentials are properly configured.

        Returns:
            True if both client_id and client_secret are provided.
        """
        return bool(self.client_id and self.client_secret)


class RedisSettings(BaseModel):
    host: str = "localhost"
    port: int = Field(default=6379, ge=1, le=65535)
    db: int = Field(default=0, ge=0, le=15)
    password: SecretStr | None = None
    ssl: bool = False

    @property
    def url(self) -> str:
        """Redis connection URL with optional authentication."""
        auth = ""
        if self.password:
            auth = f":{self.password.get_secret_value()}@"

        protocol = "rediss" if self.ssl else "redis"
        return f"{protocol}://{auth}{self.host}:{self.port}/{self.db}"


class CelerySettings(BaseModel):
    """
    Celery task queue configuration.

    Attributes:
        worker_concurrency: Number of concurrent worker processes.
        beat_enabled: Enable periodic task scheduling.
        task_track_started: Track when task starts execution.
        # TODO
    """

    worker_concurrency: int = Field(default=2, ge=1, le=10)
    beat_enabled: bool = True
    task_track_started: bool = True

    model_config = {"frozen": True}


class ApplicationSettings(BaseModel):
    """
    Core application configuration.

    Attributes:
        debug: Enable debug mode for detailed logging and diagnostics.
        api_v1_prefix: URL prefix for API version 1 endpoints.
        project_name: Display name of the application.
        version: Application version string.
    """

    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    project_name: str = "Deribit Price Tracker API"
    version: str = "0.3.0"

    model_config = {"frozen": True}

    @field_validator("api_v1_prefix")
    @classmethod
    def validate_api_prefix(cls, v: str) -> str:
        """
        Validate and normalize API URL prefix.

        Args:
            v: Raw API prefix string.

        Returns:
            Normalized API prefix with leading slash and no trailing slash.

        Raises:
            ValueError: If prefix is empty or contains invalid characters.
        """
        if not v:
            raise ValueError("API prefix cannot be empty")

        if not v.startswith("/"):
            v = f"/{v}"

        if v.endswith("/"):
            v = v.rstrip("/")

        return v


class CORSSettings(BaseModel):
    """
    Cross-Origin Resource Sharing (CORS) configuration.

    Attributes:
        origins: List of allowed origin URLs for CORS requests.
    """

    origins: list[str] = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    model_config = {"frozen": True}


class Settings(BaseSettings):
    """
    Singleton application settings class with nested configuration sections.

    Consolidates all configuration sections and loads values from
    environment variables or .env file. Uses Pydantic for validation
    and type safety with nested models.

    Environment variables follow the pattern: SECTION__FIELD_NAME
    Example: DATABASE__HOST, DERIBIT_API__CLIENT_ID
    """

    _instance: ClassVar["Settings | None"] = None

    database: DatabaseSettings
    deribit_api: DeribitAPISettings
    redis: RedisSettings
    celery: CelerySettings
    application: ApplicationSettings
    cors: CORSSettings

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="",
        env_nested_delimiter="__",
        frozen=True,
    )

    @classmethod
    def init_instance(cls, **kwargs: Any) -> "Settings":
        """
        Get singleton settings instance.

        Args:
            **kwargs: Configuration values for initial creation only.

        Returns:
            Singleton Settings instance.
        """
        if cls._instance is None:
            cls._instance = cls(**kwargs)
            cls._instance._log_initialization()

        return cls._instance

    def _log_initialization(self) -> None:
        """Log settings initialization (excluding sensitive data)."""
        self._logger = get_logger(__name__)

        if self.application.debug:
            AppLogger.set_level("DEBUG")
            self._logger.debug("Debug logging enabled")

        self._logger.debug("Debug mode: %s", self.application.debug)
        self._logger.info("Application settings initialized")

        self._logger.debug(
            "Database configured: %s:%s/%s",
            self.database.host,
            self.database.port,
            self.database.db,
        )

        self._logger.debug(
            "Redis configured: %s:%s (db: %s)",
            self.redis.host,
            self.redis.port,
            self.redis.db,
        )

        if self.deribit_api.is_configured:
            self._logger.info("Deribit API credentials configured")
        else:
            self._logger.warning(
                "Deribit API credentials not configured - "
                "only public endpoints available"
            )


def get_settings(**kwargs) -> Settings:
    """
    Get singleton settings instance.

    Returns:
        Global Settings instance.
    """
    if Settings._instance is None:
        return Settings.init_instance(**kwargs)

    return Settings._instance
