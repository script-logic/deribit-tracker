"""
Celery tasks for periodic price collection from Deribit.
"""

import asyncio
from datetime import UTC, datetime
from typing import Any

from celery import Task
from redis.asyncio.client import Redis

from app.core import get_logger, get_settings
from app.database.repository import PriceRepository

from . import celery_app
from .dependencies import get_database_manager_tasks, get_deribit_client_tasks

logger = get_logger(__name__)


async def collect_price_for_ticker(ticker: str) -> dict[str, Any] | None:
    """
    Async function to collect price for single ticker.

    Args:
        ticker: Cryptocurrency ticker symbol.

    Returns:
        Dictionary with collection result or None if failed.
    """
    from datetime import UTC, datetime

    deribit_client = get_deribit_client_tasks()
    database_manager = get_database_manager_tasks()
    timestamp = int(datetime.now(UTC).timestamp())

    try:
        price = await deribit_client.get_index_price(ticker)

        async with database_manager.get_session() as session:
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
        logger.error("Failed to collect %s price: %s", ticker, error)
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
    ignore_result=False,
)
def collect_all_prices(self: Task) -> dict[str, Any]:  # type: ignore
    """
    Celery task to collect prices for all supported tickers.

    This task is scheduled to run every minute via Celery Beat.

    Returns:
        Dictionary with collection results for all tickers.
    """
    logger.debug("Starting price collection task (sync wrapper)")

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    tickers = ["btc_usd", "eth_usd"]
    tasks: list[tuple[str, Any]] = []

    for ticker in tickers:
        task = loop.create_task(collect_price_for_ticker(ticker))
        tasks.append((ticker, task))

    results: list[dict[str, Any]] = []
    for ticker, task in tasks:
        try:
            task_result = loop.run_until_complete(task)
            results.append(task_result)
        except Exception as error:
            logger.error("Failed to collect %s price: %s", ticker, error)
            results.append(
                {"ticker": ticker, "error": str(error), "success": False},
            )

    successful = [r for r in results if r and r.get("success")]
    failed = [r for r in results if r and not r.get("success")]

    if (
        failed
        and self.max_retries is not None
        and self.request.retries < self.max_retries
    ):
        logger.warning("Some collections failed, retrying...")
        raise self.retry(countdown=30)

    result: dict[str, Any] = {
        "successful": len(successful),
        "failed": len(failed),
        "results": results,
        "timestamp": int(datetime.now(UTC).timestamp()),
    }
    return result


@celery_app.task(
    name="app.tasks.price_collection.collect_single_price",
    max_retries=2,
    ignore_result=False,
)
async def collect_single_price(ticker: str) -> dict[str, Any] | None:
    """
    Async Celery task to collect price for single ticker.

    Args:
        ticker: Cryptocurrency ticker symbol.

    Returns:
        Collection result or None if failed.
    """
    logger.info("Collecting single price for %s", ticker)

    if ticker not in ["btc_usd", "eth_usd"]:
        logger.error("Unsupported ticker: %s", ticker)
        return None

    try:
        result = await collect_price_for_ticker(ticker)
        return result

    except Exception as error:
        logger.error("Failed to collect %s price: %s", ticker, error)

        return {
            "ticker": ticker,
            "error": str(error),
            "timestamp": int(datetime.now(UTC).timestamp()),
            "success": False,
        }


@celery_app.task(
    name="app.tasks.price_collection.health_check",
    ignore_result=False,
)
def health_check() -> dict[str, Any]:
    """
    Synchronous health check task for price collection system.
    """

    async def _run_health_check() -> dict[str, Any]:
        try:
            deribit_client = get_deribit_client_tasks()
            database_manager = get_database_manager_tasks()
            api_healthy = await deribit_client.health_check()
            db_healthy = database_manager.is_initialized()
            settings = get_settings()

            redis_healthy = False
            try:
                redis_client = Redis.from_url(
                    settings.redis.url,
                    decode_responses=True,
                )
                await redis_client.ping()
                redis_healthy = True
                await redis_client.close()
            except Exception as e:
                logger.warning("Redis health check failed: %s", e)

            overall_healthy = all([api_healthy, db_healthy, redis_healthy])

            return {
                "status": "healthy" if overall_healthy else "unhealthy",
                "components": {
                    "deribit_api": (
                        "available" if api_healthy else "unavailable"
                    ),
                    "database": (
                        "initialized" if db_healthy else "not_initialized"
                    ),
                    "redis": "available" if redis_healthy else "unavailable",
                },
                "timestamp": int(datetime.now(UTC).timestamp()),
            }

        except Exception as error:
            logger.error("Health check failed: %s", error)
            return {
                "status": "unhealthy",
                "error": str(error),
                "timestamp": int(datetime.now(UTC).timestamp()),
            }

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(_run_health_check())
