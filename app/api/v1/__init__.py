"""
API version 1 router configuration.
"""

from fastapi import APIRouter

from .endpoints import prices

api_router = APIRouter()
api_router.include_router(
    prices.router,
    prefix="/prices",
    tags=["prices"],
)

__all__ = ["api_router"]
