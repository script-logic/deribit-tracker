"""
Celery tasks initialization.

This module ensures database is initialized before any task runs.
"""

from celery.signals import worker_ready

from app.core import get_logger
from app.core.celery import celery_app
from app.database.manager import database_manager

logger = get_logger(__name__)


@worker_ready.connect
def initialize_database_on_worker_start(**kwargs):
    """
    Initialize database connection when Celery worker starts.

    This ensures database_manager is ready before any tasks execute.
    """
    logger.info("Initializing database for Celery worker...")

    try:
        if not database_manager.is_initialized():
            database_manager._get_engine()
            logger.info("Database initialized for Celery worker")
        else:
            logger.info("Database already initialized")
    except Exception as e:
        logger.error("Failed to initialize database for Celery worker: %s", e)
        raise


__all__ = ["celery_app"]
