"""
Dependency injection utilities for database access.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from .manager import DatabaseManager


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI to get database session.

    Yields:
        AsyncSession: Database session.

    Usage in FastAPI:
        @app.get("/items/")
        async def read_items(session: AsyncSession = Depends(get_db_session)):
            ...
    """
    async with DatabaseManager().get_session() as session:
        yield session
