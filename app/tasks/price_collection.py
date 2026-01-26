"""
Celery tasks for periodic price collection from Deribit.

Tasks run in background to fetch cryptocurrency prices
and store them in PostgreSQL database.
"""

import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.clients import DeribitClient
from app.core import get_logger
from app.database.manager import database_manager
from app.database.repository import PriceRepository

from . import celery_app

logger = get_logger(__name__)


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database session in async tasks.

    Yields:
        AsyncSession: Database session for repository operations.
    """
    async with database_manager.get_session() as session:
        yield session


async def _collect_price_for_ticker(ticker: str) -> dict[str, Any] | None:
    """
    Collect price for single ticker and store in database.

    Args:
        ticker: Cryptocurrency ticker symbol.

    Returns:
        Dictionary with collection result or None if failed.
    """
    deribit_client = DeribitClient()
    timestamp = int(datetime.now(UTC).timestamp())

    try:
        price = await deribit_client.get_index_price(ticker)

        async with get_db_context() as session:
            repository = PriceRepository(session)
            price_tick = await repository.create(ticker, price, timestamp)
            await session.commit()

            logger.info(
                "Collected %s price: %s at %s",
                ticker,
                price,
                timestamp,
            )

            return {
                "ticker": ticker,
                "price": price,
                "timestamp": timestamp,
                "record_id": price_tick.id,
                "success": True,
            }

    except Exception as error:
        logger.error("Failed to collect %s price: %s", ticker, str(error))
        return {
            "ticker": ticker,
            "error": str(error),
            "timestamp": timestamp,
            "success": False,
        }


@celery_app.task(
    bind=True,
    name="app.tasks.price_collection.collect_all_prices",
    max_retries=3,
    default_retry_delay=30,
    acks_late=True,
)
def collect_all_prices(self) -> dict[str, Any]:
    """
    Celery task to collect prices for all supported tickers.

    This task is scheduled to run every minute via Celery Beat.

    Returns:
        Dictionary with collection results for all tickers.
    """
    logger.info("Starting price collection task")

    tickers = ["btc_usd", "eth_usd"]
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        tasks = [_collect_price_for_ticker(ticker) for ticker in tickers]
        results = loop.run_until_complete(asyncio.gather(*tasks))

        successful = [r for r in results if r and r.get("success")]
        failed = [r for r in results if r and not r.get("success")]

        if failed and self.request.retries < self.max_retries:
            logger.warning(
                "Some collections failed, retrying (%s/%s)",
                self.request.retries + 1,
                self.max_retries,
            )
            raise self.retry(countdown=30)

        return {
            "successful": len(successful),
            "failed": len(failed),
            "results": results,
            "timestamp": int(datetime.now(UTC).timestamp()),
        }

    except Exception as error:
        logger.error("Price collection task failed: %s", str(error))
        if self.request.retries < self.max_retries:
            raise self.retry(exc=error) from error
        raise

    finally:
        loop.close()


@celery_app.task(
    name="app.tasks.price_collection.collect_single_price",
    max_retries=2,
)
def collect_single_price(ticker: str) -> dict[str, Any] | None:
    """
    Celery task to collect price for single ticker.

    Args:
        ticker: Cryptocurrency ticker symbol.

    Returns:
        Collection result or None if failed.
    """
    logger.info("Collecting single price for %s", ticker)

    if ticker not in ["btc_usd", "eth_usd"]:
        logger.error("Unsupported ticker: %s", ticker)
        return None

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        result = loop.run_until_complete(_collect_price_for_ticker(ticker))
        return result

    except Exception as error:
        logger.error("Failed to collect %s price: %s", ticker, str(error))
        return None

    finally:
        loop.close()


@celery_app.task(name="app.tasks.price_collection.health_check")
def health_check() -> dict[str, Any]:
    """
    Health check task for price collection system.

    Returns:
        Dictionary with system health status.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        deribit_client = DeribitClient()
        api_healthy = loop.run_until_complete(deribit_client.health_check())

        db_healthy = database_manager.is_initialized()

        return {
            "status": "healthy" if api_healthy and db_healthy else "unhealthy",
            "deribit_api": "available" if api_healthy else "unavailable",
            "database": "initialized" if db_healthy else "not_initialized",
            "timestamp": int(datetime.now(UTC).timestamp()),
        }

    except Exception as error:
        logger.error("Health check failed: %s", str(error))
        return {
            "status": "unhealthy",
            "error": str(error),
            "timestamp": int(datetime.now(UTC).timestamp()),
        }

    finally:
        loop.close()
