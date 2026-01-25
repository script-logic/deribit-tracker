from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import description, title, version
from .core import get_logger, settings

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Deribit Price Tracker API...")
    yield
    logger.info("Shutting down Deribit Price Tracker API...")


app = FastAPI(
    title=title,
    version=version,
    description=description,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors.origins,
    allow_credentials=True,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "root"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
