from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .api import (
    api_v1_router,
    health_check_router,
    register_exception_handlers,
)
from .core import get_logger, get_settings
from .frontend import router as frontend_router


def create_app() -> FastAPI:

    logger = get_logger(__name__)

    try:
        settings = get_settings()
        app_config = settings.application
        cors_config = settings.cors
        openapi_url = "/".join([
            app_config.api_v1_prefix,
            app_config.openapi_json,
        ])

        app = FastAPI(
            title=app_config.project_name,
            version=app_config.version,
            description=app_config.description,
            docs_url=app_config.docs_url,
            redoc_url=app_config.redoc_url,
            debug=app_config.debug,
            openapi_url=openapi_url,
        )

        register_exception_handlers(app)

        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_config.origins,
            allow_credentials=cors_config.allow_credentials,
            allow_methods=cors_config.allow_methods,
            allow_headers=cors_config.allow_headers,
        )

        app.include_router(frontend_router)
        app.include_router(health_check_router)
        app.include_router(
            api_v1_router,
            prefix=app_config.api_v1_prefix,
        )

        app.mount(
            "/static",
            StaticFiles(directory="app/frontend/static"),
            name="static",
        )

        logger.info(
            "FastAPI application successfully initialized: %s",
            app_config.project_name,
        )

        return app

    except ValueError as e:
        logger.error("Configuration error: %s", e, exc_info=True)
        raise
    except Exception as e:
        logger.error(
            "Unexpected error creating FastAPI app: %s", e, exc_info=True
        )
        raise


app = create_app()
