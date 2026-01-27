"""
Core application components: configuration, logging, and database.

This module provides the foundational building blocks for the Deribit
Tracker application, including singleton settings management,
centralized logging.
"""

from .config import settings
from .logger import get_logger

__all__ = [
    "get_logger",
    "settings",
]
