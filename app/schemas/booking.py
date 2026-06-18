"""Pydantic schemas for bookings (pemesanan layanan)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import BookingStatus


class BookingCreate(BaseModel):
    provider_id: int
    service_id: int | None = None
    note: str | None = Field(default=None, max_length=1000)
    preferred_time: str | None = Field(default=None, max_length=120)


class BookingStatusUpdate(BaseModel):
    status: BookingStatus


class BookingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: BookingStatus
    note: str | None = None
    preferred_time: str | None = None
    provider_id: int
    provider_name: str
    service_id: int | None = None
    service_title: str | None = None
    customer_id: int
    customer_username: str
    created_at: datetime
