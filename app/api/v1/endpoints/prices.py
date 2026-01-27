"""
FastAPI endpoints for cryptocurrency price data.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.exceptions import NotFoundError
from app.api.v1.dependencies import get_price_service
from app.api.v1.schemas import (
    DateFilterParams,
    ErrorResponse,
    PaginationParams,
    PriceStatsResponse,
    PriceTickResponse,
)
from app.core import get_logger
from app.services.price_service import PriceService

logger = get_logger(__name__)

router = APIRouter()


@router.get(
    "/",
    response_model=list[PriceTickResponse],
    summary="Get all prices for ticker",
    description=(
        "Retrieve all price records for specified cryptocurrency ticker "
        "with pagination support."
    ),
    responses={
        400: {"model": ErrorResponse, "description": "Invalid ticker"},
        404: {"model": ErrorResponse, "description": "No prices found"},
    },
)
async def get_all_prices(
    ticker: Annotated[
        str,
        Query(
            ...,
            description="Cryptocurrency ticker symbol",
            examples=["btc_usd", "eth_usd"],
        ),
    ],
    pagination: Annotated[PaginationParams, Depends()],
    price_service: Annotated[PriceService, Depends(get_price_service)],
) -> list[PriceTickResponse]:
    """
    Get all price records for specified ticker.

    Args:
        ticker: Cryptocurrency ticker symbol (required).
        pagination: Pagination parameters (limit, offset).
        price_service: PriceService instance.

    Returns:
        List of price records.
    """
    logger.info("Getting all prices for %s", ticker)

    try:
        price_ticks = await price_service.get_all_prices(
            ticker=ticker,
            limit=pagination.limit,
            offset=pagination.offset,
        )

        if not price_ticks:
            raise NotFoundError(resource="prices", identifier=ticker)

        return [PriceTickResponse.model_validate(tick) for tick in price_ticks]

    except ValueError as error:
        logger.warning("Validation error for ticker %s: %s", ticker, error)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


@router.get(
    "/latest",
    response_model=PriceTickResponse,
    summary="Get latest price",
    description="Retrieve the most recent price for specified ticker.",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid ticker"},
        404: {"model": ErrorResponse, "description": "No prices found"},
    },
)
async def get_latest_price(
    ticker: Annotated[
        str,
        Query(
            ...,
            description="Cryptocurrency ticker symbol",
            examples=["btc_usd", "eth_usd"],
        ),
    ],
    price_service: Annotated[PriceService, Depends(get_price_service)],
) -> PriceTickResponse:
    """
    Get latest price for ticker.

    Args:
        ticker: Cryptocurrency ticker symbol (required).
        price_service: PriceService instance.

    Returns:
        Latest price record.
    """
    logger.info("Getting latest price for %s", ticker)

    try:
        price_tick = await price_service.get_latest_price(ticker)

        if price_tick is None:
            raise NotFoundError(resource="latest_price", identifier=ticker)

        result: PriceTickResponse = PriceTickResponse.model_validate(
            price_tick,
        )
        return result

    except ValueError as error:
        logger.warning("Validation error for ticker %s: %s", ticker, error)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


@router.get(
    "/at-timestamp",
    response_model=PriceTickResponse,
    summary="Get price at timestamp",
    description="Retrieve price at exact UNIX timestamp.",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid parameters"},
        404: {"model": ErrorResponse, "description": "Price not found"},
    },
)
async def get_price_at_timestamp(
    ticker: Annotated[
        str,
        Query(
            ...,
            description="Cryptocurrency ticker symbol",
            examples=["btc_usd", "eth_usd"],
        ),
    ],
    timestamp: Annotated[
        int,
        Query(
            ...,
            description="UNIX timestamp",
            examples=[1700000000],
            ge=0,
        ),
    ],
    price_service: Annotated[PriceService, Depends(get_price_service)],
) -> PriceTickResponse:
    """
    Get price at exact timestamp.

    Args:
        ticker: Cryptocurrency ticker symbol (required).
        timestamp: UNIX timestamp (required).
        price_service: PriceService instance.

    Returns:
        Price record at specified timestamp.
    """
    logger.info(
        "Getting price for %s at timestamp %s",
        ticker,
        timestamp,
    )

    try:
        price_tick = await price_service.get_price_at_timestamp(
            ticker=ticker,
            timestamp=timestamp,
        )

        if price_tick is None:
            raise NotFoundError(resource="price_at_timestamp", identifier="")

        result: PriceTickResponse = PriceTickResponse.model_validate(
            price_tick,
        )
        return result

    except ValueError as error:
        logger.warning(
            "Validation error for %s at %s: %s",
            ticker,
            timestamp,
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


@router.get(
    "/closest-to-timestamp",
    response_model=PriceTickResponse,
    summary="Get price closest to timestamp",
    description=(
        "Retrieve price closest to specified UNIX timestamp "
        "within 60 seconds window."
    ),
    responses={
        400: {"model": ErrorResponse, "description": "Invalid parameters"},
        404: {"model": ErrorResponse, "description": "Price not found"},
    },
)
async def get_price_closest_to_timestamp(
    ticker: Annotated[
        str,
        Query(
            ...,
            description="Cryptocurrency ticker symbol",
            examples=["btc_usd", "eth_usd"],
        ),
    ],
    timestamp: Annotated[
        int,
        Query(
            ...,
            description="UNIX timestamp",
            examples=[1700000000],
            ge=0,
        ),
    ],
    price_service: Annotated[PriceService, Depends(get_price_service)],
    max_difference: Annotated[
        int,
        Query(
            description="Maximum time difference in seconds",
            ge=1,
            le=3600,
            alias="maxDifference",
        ),
    ] = 60,
) -> PriceTickResponse:
    """
    Get price closest to timestamp.

    Args:
        ticker: Cryptocurrency ticker symbol (required).
        timestamp: Target UNIX timestamp (required).
        max_difference: Maximum time difference in seconds.
        price_service: PriceService instance.

    Returns:
        Closest price record.
    """
    logger.info(
        "Getting price closest to %s for %s (±%s seconds)",
        timestamp,
        ticker,
        max_difference,
    )

    try:
        price_tick = await price_service.get_price_closest_to_timestamp(
            ticker=ticker,
            timestamp=timestamp,
            max_difference_seconds=max_difference,
        )

        if price_tick is None:
            raise NotFoundError(
                resource="price_closest_to_timestamp",
                identifier="",
            )

        result: PriceTickResponse = PriceTickResponse.model_validate(
            price_tick,
        )
        return result

    except ValueError as error:
        logger.warning(
            "Validation error for %s closest to %s: %s",
            ticker,
            timestamp,
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


@router.get(
    "/by-date",
    response_model=list[PriceTickResponse],
    summary="Get prices by date range",
    description="Retrieve prices within specified date range.",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid parameters"},
        404: {"model": ErrorResponse, "description": "No prices found"},
    },
)
async def get_prices_by_date(
    ticker: Annotated[
        str,
        Query(
            ...,
            description="Cryptocurrency ticker symbol",
            examples=["btc_usd", "eth_usd"],
        ),
    ],
    date_filter: Annotated[DateFilterParams, Depends()],
    price_service: Annotated[PriceService, Depends(get_price_service)],
) -> list[PriceTickResponse]:
    """
    Get prices by date range.

    Args:
        ticker: Cryptocurrency ticker symbol (required).
        date_filter: Date range filter parameters.
        price_service: PriceService instance.

    Returns:
        List of price records within date range.
    """
    logger.info(
        "Getting prices for %s from %s to %s",
        ticker,
        date_filter.start_date,
        date_filter.end_date,
    )

    try:
        price_ticks = await price_service.get_prices_by_date_range(
            ticker=ticker,
            start_date=date_filter.start_date,
            end_date=date_filter.end_date,
        )

        if not price_ticks:
            raise NotFoundError(resource="prices_by_date", identifier=ticker)

        return [PriceTickResponse.model_validate(tick) for tick in price_ticks]

    except ValueError as error:
        logger.warning(
            "Validation error for %s date filter: %s",
            ticker,
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


@router.get(
    "/stats",
    response_model=PriceStatsResponse,
    summary="Get price statistics",
    description="Retrieve comprehensive statistics for ticker.",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid parameters"},
        404: {"model": ErrorResponse, "description": "No prices found"},
    },
)
async def get_price_statistics(
    ticker: Annotated[
        str,
        Query(
            ...,
            description="Cryptocurrency ticker symbol",
            examples=["btc_usd", "eth_usd"],
        ),
    ],
    price_service: Annotated[PriceService, Depends(get_price_service)],
    timestamp: Annotated[
        int | None,
        Query(
            description="Optional target timestamp for specific price",
            examples=[1700000000],
            ge=0,
        ),
    ] = None,
) -> PriceStatsResponse:
    """
    Get price statistics.

    Args:
        ticker: Cryptocurrency ticker symbol (required).
        timestamp: Optional target timestamp.
        price_service: PriceService instance.

    Returns:
        Comprehensive price statistics.
    """
    logger.info("Getting statistics for %s", ticker)

    try:
        stats = await price_service.get_price_statistics(
            ticker=ticker,
            target_timestamp=timestamp,
        )

        if stats["count"] == 0:
            raise NotFoundError(resource="price_statistics", identifier=ticker)

        result: PriceStatsResponse = PriceStatsResponse.model_validate(stats)
        return result

    except ValueError as error:
        logger.warning(
            "Validation error for %s statistics: %s",
            ticker,
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
