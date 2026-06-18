"""Aggregate router mounting all v1 API routes."""

from fastapi import APIRouter

from app.api.routes import auth, providers

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(providers.router)
