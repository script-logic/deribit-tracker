"""
Database connection and session management.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core import get_logger, settings

from .base import Base

logger = get_logger(__name__)


class DatabaseManager:
    """
    Manages database connections and sessions.
    """

    def __init__(self) -> None:
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    def _get_engine(self) -> AsyncEngine:
        """
        Get or create engine with lazy initialization.

        Returns:
            AsyncEngine instance.

        Raises:
            RuntimeError: If engine cannot be created.
        """
        if self._engine is None:
            self._engine = create_async_engine(
                settings.database.async_dsn,
                echo=settings.application.debug,
                pool_pre_ping=True,
                pool_recycle=300,
                pool_size=20,
                max_overflow=30,
            )
        return self._engine

    def _get_session_factory(self) -> async_sessionmaker[AsyncSession]:
        """
        Get or create session factory with lazy initialization.

        Returns:
            async_sessionmaker instance.

        Raises:
            RuntimeError: If session factory cannot be created.
        """
        if self._session_factory is None:
            self._session_factory = async_sessionmaker(
                bind=self._get_engine(),
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False,
            )
        return self._session_factory

    async def create_all(self) -> None:
        """Create all database tables."""
        async with self._get_engine().begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    async def drop_all(self) -> None:
        """Drop all database tables."""
        async with self._get_engine().begin() as connection:
            await connection.run_sync(Base.metadata.drop_all)

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Context manager for database sessions.

        Yields:
            AsyncSession: Database session.
        """
        session = self._get_session_factory()()

        try:
            yield session
            await session.commit()
        except Exception as error:
            await session.rollback()
            raise error
        finally:
            await session.close()

    async def dispose(self) -> None:
        """Close all database connections."""
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None

    def is_initialized(self) -> bool:
        """
        Check if database is initialized.

        Returns:
            True if engine and session factory are initialized.
        """
        return self._engine is not None and self._session_factory is not None


database_manager = DatabaseManager()
database_manager._get_engine()
database_manager._get_session_factory()
