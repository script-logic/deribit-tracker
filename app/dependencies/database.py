"""
Dependency injection utilities for database access.
"""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import DatabaseManager


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI to get database session.

    Returns an async generator that FastAPI can use.
    """
    database_manager = DatabaseManager()

    async for session in database_manager.get_session_generator():
        yield session


DatabaseSession = Annotated[AsyncSession, Depends(get_db_session)]
