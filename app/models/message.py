"""Message ORM model — in-app chat tied to a booking (obrolan pesanan)."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class Message(Base):
    """A chat message between a resident and a provider within a booking."""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    booking_id: Mapped[int] = mapped_column(
        ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sender_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    sender: Mapped["User"] = relationship(lazy="selectin")

    @property
    def sender_username(self) -> str:
        return self.sender.username if self.sender else "pengguna"

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Message id={self.id} booking={self.booking_id}>"
