"""Yorozuya FastAPI application entrypoint."""

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    description="Yorozuya — a do-anything service backend (FastAPI + PostgreSQL).",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Simple liveness probe."""
    return {"status": "ok"}


@app.get("/", tags=["health"])
async def root() -> dict[str, str]:
    return {"service": settings.PROJECT_NAME, "docs": "/docs"}
