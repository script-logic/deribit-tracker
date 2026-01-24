"""
Database module package exports.

Provides clean, minimal exports for database functionality.
"""

from .base import Base
from .deps import get_db_session
from .manager import DatabaseManager

__all__ = [
    "Base",
    "database_manager",
    "get_db_session",
]

database_manager = DatabaseManager()
