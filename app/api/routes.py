"""
API version 1 router configuration.
"""

from fastapi import APIRouter

from .v1.endpoints import prices_router

api_v1_router = APIRouter()
root_router = APIRouter()
health_check_router = APIRouter()


@root_router.get("/")
async def root():
    return {"message": "Deribit Price Tracker API is running"}


@health_check_router.get("/health")
async def health_check():
    return {"status": "healthy"}


api_v1_router.include_router(
    prices_router,
    prefix="/prices",
    tags=["prices"],
)
