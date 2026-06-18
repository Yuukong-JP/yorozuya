"""Booking ORM model (pemesanan layanan)."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import BookingStatus

if TYPE_CHECKING:
    from app.models.provider import ProviderProfile, Service
    from app.models.user import User


class Booking(Base):
    """A request from a resident (warga) to hire a provider for a service."""

    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider_id: Mapped[int] = mapped_column(
        ForeignKey("provider_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    service_id: Mapped[int | None] = mapped_column(
        ForeignKey("services.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default=BookingStatus.PENDING.value,
        server_default=BookingStatus.PENDING.value,
        nullable=False,
        index=True,
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    preferred_time: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    customer: Mapped["User"] = relationship(lazy="selectin")
    provider: Mapped["ProviderProfile"] = relationship(lazy="selectin")
    service: Mapped["Service | None"] = relationship(lazy="selectin")

    @property
    def customer_username(self) -> str:
        return self.customer.username if self.customer else "warga"

    @property
    def provider_name(self) -> str:
        return self.provider.display_name if self.provider else ""

    @property
    def service_title(self) -> str | None:
        return self.service.title if self.service else None

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Booking id={self.id} status={self.status} provider={self.provider_id}>"
