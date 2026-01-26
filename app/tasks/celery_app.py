"""
Celery application entry point.

This module exports the Celery app instance for use with
celery command line interface.
"""

from app.core.celery import celery_app

__all__ = ["celery_app"]
