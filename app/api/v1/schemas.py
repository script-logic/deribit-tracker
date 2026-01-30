"""
Pydantic schemas for API request/response validation.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PriceTickBase(BaseModel):
    """Base schema for price tick data."""

    ticker: str = Field(
        ...,
        description="Cryptocurrency ticker symbol",
        examples=["btc_usd", "eth_usd"],
    )
    price: float = Field(
        ...,
        description="Current index price in USD",
        examples=[45000.50, 2500.75],
        ge=0,
    )
    timestamp: int = Field(
        ...,
        description="UNIX timestamp when price was recorded",
        examples=[1700000000],
        ge=0,
    )


class PriceTickCreate(PriceTickBase):
    """Schema for creating new price tick."""

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        """Validate ticker format."""
        v = v.strip().lower()
        if v not in {"btc_usd", "eth_usd"}:
            raise ValueError(
                f"Unsupported ticker: {v}. Supported: 'btc_usd', 'eth_usd'"
            )
        return v


class PriceTickResponse(PriceTickBase):
    """Schema for price tick response."""

    id: int = Field(..., description="Unique identifier")
    created_at: datetime = Field(..., description="Record creation timestamp")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "ticker": "btc_usd",
                "price": 45000.50,
                "timestamp": 1700000000,
                "created_at": "2026-01-01T00:00:00Z",
            }
        },
    )


class PriceCollectionResponse(BaseModel):
    """Schema for price collection task response."""

    successful: int = Field(
        ...,
        description="Number of successful collections",
    )
    failed: int = Field(..., description="Number of failed collections")
    timestamp: int = Field(..., description="Collection timestamp")
    results: list[dict[str, Any]] | None = Field(
        default=None,
        description="Detailed collection results",
    )


class ErrorResponse(BaseModel):
    """Schema for error responses."""

    detail: str = Field(..., description="Error description")
    error_type: str | None = Field(default=None, description="Error type")


class PaginationParams(BaseModel):
    """Schema for pagination parameters."""

    limit: int = Field(
        default=100,
        description="Maximum number of records to return",
        ge=1,
        le=1000,
    )
    offset: int = Field(
        default=0,
        description="Number of records to skip",
        ge=0,
    )


class DateFilterParams(BaseModel):
    """Schema for date filtering parameters."""

    start_date: datetime | None = Field(
        default=None,
        description="Start date for filtering (inclusive)",
        examples=["2026-01-01T00:00:00Z"],
    )
    end_date: datetime | None = Field(
        default=None,
        description="End date for filtering (inclusive)",
        examples=["2026-01-02T00:00:00Z"],
    )


class PriceStatsResponse(BaseModel):
    """Schema for price statistics."""

    ticker: str = Field(..., description="Cryptocurrency ticker symbol")
    latest_price: float | None = Field(
        default=None,
        description="Latest price recorded",
    )
    latest_timestamp: int | None = Field(
        default=None,
        description="Timestamp of latest price",
    )
    count: int = Field(..., description="Total number of records")
    price_at_time: float | None = Field(
        default=None,
        description="Price at requested timestamp",
    )
    closest_price: float | None = Field(
        default=None,
        description="Price closest to requested timestamp",
    )
    min_price: float | None = Field(default=None, description="Minimum price")
    max_price: float | None = Field(default=None, description="Maximum price")
    avg_price: float | None = Field(default=None, description="Average price")
