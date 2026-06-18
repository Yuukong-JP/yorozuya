"""Provider profile and service ORM models."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class ProviderProfile(Base):
    """Public-facing profile of an informal worker (penyedia)."""

    __tablename__ = "provider_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    profession: Mapped[str] = mapped_column(String(100), nullable=False)
    headline: Mapped[str | None] = mapped_column(String(200), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    city: Mapped[str] = mapped_column(
        String(100), default="Padang Panjang", server_default="Padang Panjang"
    )
    area: Mapped[str | None] = mapped_column(String(150), nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship(lazy="selectin")
    services: Mapped[list["Service"]] = relationship(
        back_populates="provider",
        cascade="all, delete-orphan",
        order_by="Service.created_at.desc()",
    )
    reviews: Mapped[list["Review"]] = relationship(
        back_populates="provider",
        cascade="all, delete-orphan",
        order_by="Review.created_at.desc()",
    )

    @property
    def is_verified(self) -> bool:
        """Expose the owning user's verification status on the profile."""
        return bool(self.user and self.user.is_verified)

    @property
    def rating_count(self) -> int:
        return len(self.reviews)

    @property
    def rating_avg(self) -> float:
        if not self.reviews:
            return 0.0
        return round(sum(r.rating for r in self.reviews) / len(self.reviews), 1)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ProviderProfile id={self.id} name={self.display_name!r}>"


class Service(Base):
    """A service package offered by a provider (paket layanan)."""

    __tablename__ = "services"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    provider_id: Mapped[int] = mapped_column(
        ForeignKey("provider_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    price: Mapped[int] = mapped_column(Integer, nullable=False)  # Rupiah
    price_unit: Mapped[str] = mapped_column(
        String(30), default="per pekerjaan", server_default="per pekerjaan"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    provider: Mapped["ProviderProfile"] = relationship(back_populates="services")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Service id={self.id} title={self.title!r}>"


class Review(Base):
    """A rating + comment left by a resident for a provider (ulasan)."""

    __tablename__ = "reviews"
    __table_args__ = (
        UniqueConstraint(
            "provider_id", "author_id", name="uq_review_provider_author"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    provider_id: Mapped[int] = mapped_column(
        ForeignKey("provider_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1..5
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    provider: Mapped["ProviderProfile"] = relationship(back_populates="reviews")
    author: Mapped["User"] = relationship(lazy="selectin")

    @property
    def author_username(self) -> str:
        return self.author.username if self.author else "warga"

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Review id={self.id} provider={self.provider_id} rating={self.rating}>"
