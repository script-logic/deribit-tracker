from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import (
    description,
    title,
    version,
)

app = FastAPI(
    title=title,
    version=version,
    description=description,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],  # TODO: get
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "root"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
