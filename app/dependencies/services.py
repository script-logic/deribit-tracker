from typing import Annotated

from fastapi import Depends

from app.core import get_logger
from app.database import PriceRepository
from app.services import PriceService

from .database import DatabaseSession

logger = get_logger(__name__)


def get_price_service(
    session: DatabaseSession,
) -> PriceService:
    """
    Dependency for FastAPI for PriceService.
    """
    repository = PriceRepository(session)
    return PriceService(repository)


PriceServiceDep = Annotated[PriceService, Depends(get_price_service)]
