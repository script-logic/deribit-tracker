"""
Core application components: configuration, logging, and database.

This module provides the foundational building blocks for the Deribit
Tracker application, including singleton settings management,
centralized logging.
"""

from .config import get_settings
from .logger import get_logger

logger = get_logger(__name__)


try:
    settings = get_settings()
except Exception as e:
    logger.error("Failed to initialize settings: %s", e)
    raise

__all__ = [
    "get_logger",
    "get_settings",
]
