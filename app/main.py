"""KOLEGA FastAPI application entrypoint."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

import app.models  # noqa: F401 — register ORM models on Base.metadata
from app.api.router import api_router
from app.core.config import settings
from app.core.database import Base, engine

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """On the zero-setup SQLite default, create tables automatically so the app
    runs without an Alembic migration step. PostgreSQL still uses Alembic."""
    if settings.DATABASE_IS_SQLITE:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    description=(
        "KOLEGA (Kolaborasi Layanan Ekonomi & Geliat Warga) — a hyperlocal "
        "platform connecting informal workers with residents who need their "
        "services. Built with FastAPI."
    ),
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Simple liveness probe."""
    return {"status": "ok"}


# Serve the single-page web client at the root. Mounted last so it does not
# shadow the API (/api/v1) or /health routes registered above.
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="frontend")
