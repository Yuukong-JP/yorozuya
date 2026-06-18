"""Pydantic schemas for provider services (paket layanan)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ServiceCategory


class ServiceBase(BaseModel):
    title: str = Field(min_length=3, max_length=150)
    description: str | None = Field(default=None, max_length=2000)
    category: ServiceCategory
    price: int = Field(ge=0, description="Harga dalam Rupiah")
    price_unit: str = Field(default="per pekerjaan", max_length=30)


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=150)
    description: str | None = Field(default=None, max_length=2000)
    category: ServiceCategory | None = None
    price: int | None = Field(default=None, ge=0)
    price_unit: str | None = Field(default=None, max_length=30)
    is_active: bool | None = None


class ServiceRead(ServiceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    provider_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
