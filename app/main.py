from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import project_metadata
from .api import api_v1_router, health_check_router, root_router
from .api.exceptions import register_exception_handlers
from .core import get_logger, settings

logger = get_logger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title=project_metadata["title"],
        version=project_metadata["version"],
        description=project_metadata["description"],
        openapi_url=f"{settings.application.api_v1_prefix}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        debug=settings.application.debug,
    )

    register_exception_handlers(app)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors.origins,
        allow_credentials=True,
        allow_methods=["GET", "OPTIONS"],
        allow_headers=["*"],
    )

    app.include_router(
        api_v1_router,
        prefix=settings.application.api_v1_prefix,
    )
    app.include_router(root_router)
    app.include_router(health_check_router)

    return app


try:
    app: FastAPI = create_app()
except Exception as e:
    logger.error("FastAPI app creation error: %s", e)
    raise
