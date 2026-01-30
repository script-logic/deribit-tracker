"""
Frontend route handlers.

Serves the HTML interface for the application using Jinja2 templates.
"""

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core import get_logger, get_settings

logger = get_logger(__name__)

router = APIRouter()


def get_templates() -> Jinja2Templates:
    """
    Locate and initialize Jinja2 templates.
    """
    base_path = Path(__file__).parent
    return Jinja2Templates(directory=base_path / "templates")


@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request) -> HTMLResponse:
    """
    Serve the main dashboard.

    Args:
        request: The incominng HTTP request.

    Returns:
        Rendered HTML dashboard.
    """
    settings = get_settings()
    templates = get_templates()

    logger.info("Serving frontend dashboard to client")

    return templates.TemplateResponse(
        name="index.html",
        context={
            "request": request,
            "project_name": settings.application.project_name,
            "api_v1_prefix": settings.application.api_v1_prefix,
            "version": settings.application.version,
        },
    )
