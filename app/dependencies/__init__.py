"""
Centralized dependency injection for FastAPI application.
"""

from .clients import DeribitClientDep
from .database import DatabaseSession
from .services import PriceServiceDep

__all__ = [
    "DatabaseSession",
    "DeribitClientDep",
    "PriceServiceDep",
]
