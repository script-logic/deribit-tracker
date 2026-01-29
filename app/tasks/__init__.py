"""
Celery tasks initialization.

This module ensures database is initialized before any task runs.
"""

from .celery_application import celery_app

__all__ = ["celery_app"]
