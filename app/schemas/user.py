"""Pydantic schemas for user resources."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import UserRole


class RegistrationRole(str, Enum):
    """Roles a user may self-register as. Admin accounts are provisioned
    internally and cannot be created through the public API."""

    CUSTOMER = UserRole.CUSTOMER.value
    PROVIDER = UserRole.PROVIDER.value


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)
    role: RegistrationRole = RegistrationRole.CUSTOMER


class UserLogin(BaseModel):
    username: str
    password: str


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: UserRole
    is_verified: bool
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
