"""Database operations for bookings (pemesanan layanan)."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.enums import BookingStatus
from app.schemas.booking import BookingCreate


async def get_booking(db: AsyncSession, booking_id: int) -> Booking | None:
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    return result.scalar_one_or_none()


async def create_booking(
    db: AsyncSession, customer_id: int, data: BookingCreate
) -> Booking:
    booking = Booking(
        customer_id=customer_id,
        provider_id=data.provider_id,
        service_id=data.service_id,
        note=data.note,
        preferred_time=data.preferred_time,
        status=BookingStatus.PENDING.value,
    )
    db.add(booking)
    await db.commit()
    return await get_booking(db, booking.id)


async def list_customer_bookings(
    db: AsyncSession, customer_id: int
) -> list[Booking]:
    result = await db.execute(
        select(Booking)
        .where(Booking.customer_id == customer_id)
        .order_by(Booking.created_at.desc())
    )
    return list(result.scalars().all())


async def list_provider_bookings(
    db: AsyncSession, provider_id: int
) -> list[Booking]:
    result = await db.execute(
        select(Booking)
        .where(Booking.provider_id == provider_id)
        .order_by(Booking.created_at.desc())
    )
    return list(result.scalars().all())


async def set_status(
    db: AsyncSession, booking: Booking, status: BookingStatus
) -> Booking:
    booking.status = status.value
    await db.commit()
    return await get_booking(db, booking.id)
