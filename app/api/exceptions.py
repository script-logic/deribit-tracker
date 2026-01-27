"""
Custom exceptions and error handlers for API error handling.
"""

from typing import Any, cast

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core import get_logger

logger = get_logger(__name__)


class APIError(HTTPException):
    """Base exception for API errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_type: str = "api_error",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(status_code=status_code, detail=message)
        self.error_type = error_type
        self.details = details or {}


class ValidationError(APIError):
    """Raised when request validation fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_type="validation_error",
            details=details,
        )


class NotFoundError(APIError):
    """Raised when requested resource is not found."""

    def __init__(self, resource: str, identifier: str | None = None):
        if identifier:
            message = f"{resource} '{identifier}' not found"
        else:
            message = f"{resource} not found"

        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_type="not_found",
            details={"resource": resource, "identifier": identifier},
        )


class ServiceUnavailableError(APIError):
    """Raised when external service is unavailable."""

    def __init__(self, service: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=f"{service} service is temporarily unavailable",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_type="service_unavailable",
            details={"service": service, **(details or {})},
        )


async def http_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle HTTPException and APIError."""
    if not isinstance(exc, HTTPException):
        raise exc

    if isinstance(exc, APIError):
        logger.warning(
            "API error: %s (status: %s, type: %s)",
            exc.detail,
            exc.status_code,
            exc.error_type,
            extra={"details": exc.details},
        )

        response_content = {
            "detail": cast(str, exc.detail),
            "error_type": exc.error_type,
            "details": exc.details,
        }
    else:
        logger.warning(
            "HTTP exception: %s (status: %s)",
            exc.detail,
            exc.status_code,
        )

        response_content = {
            "detail": str(exc.detail),
            "error_type": "http_error",
        }

    return JSONResponse(
        status_code=exc.status_code,
        content=response_content,
    )


async def validation_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle validation errors."""
    if not isinstance(exc, RequestValidationError):
        raise exc

    logger.warning(
        "Validation error: %s",
        exc.errors(),
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation failed",
            "error_type": "validation_error",
            "errors": exc.errors(),
        },
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle all other exceptions."""
    logger.error(
        "Unhandled exception: %s",
        exc,
        exc_info=True,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "error_type": "internal_error",
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers for FastAPI app."""
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(
        RequestValidationError,
        validation_exception_handler,
    )
    app.add_exception_handler(Exception, generic_exception_handler)
