from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import description, title, version
from .api import api_router
from .api.exceptions import register_exception_handlers
from .core import get_logger, settings

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Deribit Price Tracker API...")
    yield
    logger.info("Shutting down Deribit Price Tracker API...")


def create_app() -> FastAPI:
    app = FastAPI(
        title=title,
        version=version,
        description=description,
        lifespan=lifespan,
        openapi_url=f"{settings.application.api_v1_prefix}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
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
        api_router,
        prefix=settings.application.api_v1_prefix,
    )

    return app


try:
    app: FastAPI = create_app()
except Exception as e:
    logger.error("FastAPI app creation error: %s", e)
    raise


@app.get("/")
async def root():
    return {"message": "Deribit Price Tracker API is running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
