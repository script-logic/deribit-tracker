from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_logger
from app.database.deps import get_db_session
from app.database.repository import PriceRepository
from app.services.price_service import PriceService

logger = get_logger(__name__)


def get_price_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> PriceService:
    """Dependency for PriceService."""
    repository = PriceRepository(session)
    return PriceService(repository)
