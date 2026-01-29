"""
Application configuration management with environment-based settings.

Uses Pydantic for type-safe configuration with support for nested models,
environment variable loading, and singleton pattern for global access.
"""

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any, ClassVar

import toml
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
    project_name: str = ""
    version: str = ""
    description: str = ""
    openapi_json: str = "openapi.json"
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"

    model_config = {"frozen": True}

    def __init__(self, **data: dict[str, Any]):
        super().__init__(**data)

        metadata = self._get_metadata()

        if not self.project_name:
            object.__setattr__(
                self, "project_name", metadata.get("title", "Unknown")
            )
        if not self.version:
            object.__setattr__(
                self, "version", metadata.get("version", "Unknown")
            )
        if not self.description:
            object.__setattr__(
                self, "description", metadata.get("description", "")
            )

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

    @property
    def metadata(self) -> dict[str, str]:
        return self._get_metadata()

    def _get_metadata(self) -> dict[str, str]:
        """
        Retrieves application metadata from the installed package information.

        Returns:
            dict:
                version (str): Current application version (e.g., "0.4.0")
                description (str): Brief application description
                title (str): Formatted title (e.g., "Deribit Tracker")
        """
        pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"

        try:
            data = toml.load(pyproject_path)

            project_section = data.get("project", {})

            return {
                "version": project_section.get("version", "Unknown"),
                "description": project_section.get("description", ""),
                "title": project_section
                .get("name", "Unknown")
                .replace("-", " ")
                .title(),
            }
        except Exception as e:
            logging.getLogger(__name__).warning(
                "Could not read pyproject.toml: %s", e
            )

        return {
            "title": "Unknown",
            "version": "Unknown",
            "description": "",
        }


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
    allow_credentials: bool = True
    allow_methods: list[str] = ["GET", "OPTIONS"]
    allow_headers: list[str] = ["*"]

    model_config = {"frozen": True}


class Settings(BaseSettings):
    """
    Singleton application settings class with nested configuration sections.

    Consolidates all configuration sections and loads values from
    environment variables or .env file. Uses Pydantic for validation
    and type safety with nested models.
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
        logger = get_logger(__name__)

        if self.application.debug:
            AppLogger.set_level("DEBUG")
            logger.debug("Debug logging enabled")

        logger.debug("Debug mode: %s", self.application.debug)
        logger.info("Application settings initialized")

        logger.debug(
            "Database configured: %s:%s/%s",
            self.database.host,
            self.database.port,
            self.database.db,
        )

        logger.debug(
            "Redis configured: %s:%s (db: %s)",
            self.redis.host,
            self.redis.port,
            self.redis.db,
        )

        if self.deribit_api.is_configured:
            logger.info("Deribit API credentials configured")
        else:
            logger.warning(
                "Deribit API credentials not configured - "
                "only public endpoints available"
            )


@lru_cache
def get_settings() -> Settings:
    """
    Get singleton settings instance.

    Returns:
        Global Settings instance.
    """
    return Settings.init_instance()
