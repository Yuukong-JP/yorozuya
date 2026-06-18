"""Aggregate router mounting all v1 API routes."""

from fastapi import APIRouter

from app.api.routes import admin, auth, bookings, providers

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(providers.router)
api_router.include_router(bookings.router)
api_router.include_router(admin.router)
