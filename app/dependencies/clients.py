"""
Dependencies for external service clients.
"""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends, HTTPException

from app.clients import DeribitClient
from app.core import get_logger, get_settings

logger = get_logger(__name__)


@lru_cache
def _get_cached_deribit_client(base_url: str) -> DeribitClient:
    """Internal cached factory for Deribit client."""
    return DeribitClient(base_url=base_url)


async def get_deribit_client() -> DeribitClient:
    """
    FastAPI dependency for Deribit client.

    Returns cached client with settings injection.
    """
    try:
        settings = get_settings()

        logger.debug(
            "Creating Deribit client for %s", settings.deribit_api.base_url
        )
        client = _get_cached_deribit_client(
            base_url=settings.deribit_api.base_url
        )

        if not await client.health_check():
            logger.warning("Deribit API is not available")

        return client

    except Exception as e:
        logger.error("Failed to create Deribit client: %s", e, exc_info=True)
        raise HTTPException(
            status_code=503, detail="Deribit service is unavailable"
        ) from e


DeribitClientDep = Annotated[DeribitClient, Depends(get_deribit_client)]
