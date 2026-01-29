"""
Celery task dependencies.
"""

from functools import lru_cache

from app.clients import DeribitClient
from app.core import get_settings
from app.database import DatabaseManager


@lru_cache
def get_database_manager_tasks() -> DatabaseManager:
    """Get cached database manager."""
    return DatabaseManager()


@lru_cache
def get_deribit_client_tasks() -> DeribitClient:
    """Get Deribit client for Celery tasks."""
    settings = get_settings()
    return DeribitClient(base_url=settings.deribit_api.base_url)
