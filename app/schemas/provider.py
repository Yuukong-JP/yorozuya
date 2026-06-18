"""Pydantic schemas for provider profiles (penyedia)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.review import ReviewRead
from app.schemas.service import ServiceRead


class ProviderProfileBase(BaseModel):
    display_name: str = Field(min_length=2, max_length=100)
    profession: str = Field(min_length=2, max_length=100)
    headline: str | None = Field(default=None, max_length=200)
    bio: str | None = Field(default=None, max_length=4000)
    phone: str | None = Field(default=None, max_length=30)
    city: str = Field(default="Padang Panjang", max_length=100)
    area: str | None = Field(default=None, max_length=150)
    photo_url: str | None = Field(default=None, max_length=500)


class ProviderProfileCreate(ProviderProfileBase):
    pass


class ProviderProfileUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=2, max_length=100)
    profession: str | None = Field(default=None, min_length=2, max_length=100)
    headline: str | None = Field(default=None, max_length=200)
    bio: str | None = Field(default=None, max_length=4000)
    phone: str | None = Field(default=None, max_length=30)
    city: str | None = Field(default=None, max_length=100)
    area: str | None = Field(default=None, max_length=150)
    photo_url: str | None = Field(default=None, max_length=500)


class ProviderSummary(ProviderProfileBase):
    """Lightweight provider entry for browse/search listings."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    is_verified: bool = False
    service_count: int = 0
    starting_price: int | None = None
    primary_category: str | None = None
    rating_avg: float = 0.0
    rating_count: int = 0


class ProviderProfileRead(ProviderProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    is_verified: bool = False
    services: list[ServiceRead] = []
    reviews: list[ReviewRead] = []
    rating_avg: float = 0.0
    rating_count: int = 0
    created_at: datetime
    updated_at: datetime
