"""Booking routes (pemesanan layanan)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_current_provider
from app.core.database import get_db
from app.crud import booking as booking_crud
from app.crud import provider as provider_crud
from app.models.enums import BookingStatus
from app.models.user import User
from app.schemas.booking import BookingCreate, BookingRead, BookingStatusUpdate

router = APIRouter(prefix="/bookings", tags=["bookings"])

# Statuses a provider is allowed to set on an incoming booking.
_PROVIDER_STATUSES = {
    BookingStatus.ACCEPTED,
    BookingStatus.REJECTED,
    BookingStatus.COMPLETED,
}


@router.post("", response_model=BookingRead, status_code=status.HTTP_201_CREATED)
async def create_booking(
    data: BookingCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> BookingRead:
    provider = await provider_crud.get_profile_by_id(db, data.provider_id)
    if provider is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Penyedia tidak ditemukan"
        )
    if provider.user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tidak bisa memesan jasa sendiri",
        )
    if data.service_id is not None:
        service = await provider_crud.get_service(db, data.service_id)
        if service is None or service.provider_id != provider.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Layanan tidak ditemukan untuk penyedia ini",
            )
    return await booking_crud.create_booking(db, current_user.id, data)


@router.get("/me", response_model=list[BookingRead])
async def list_my_bookings(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[BookingRead]:
    """Bookings I placed as a resident (warga)."""
    return await booking_crud.list_customer_bookings(db, current_user.id)


@router.get("/incoming", response_model=list[BookingRead])
async def list_incoming_bookings(
    current_user: User = Depends(get_current_provider),
    db: AsyncSession = Depends(get_db),
) -> list[BookingRead]:
    """Bookings addressed to my provider profile (penyedia)."""
    profile = await provider_crud.get_profile_by_user(db, current_user.id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Buat profil penyedia terlebih dahulu",
        )
    return await booking_crud.list_provider_bookings(db, profile.id)


@router.post("/{booking_id}/status", response_model=BookingRead)
async def update_booking_status(
    booking_id: int,
    data: BookingStatusUpdate,
    current_user: User = Depends(get_current_provider),
    db: AsyncSession = Depends(get_db),
) -> BookingRead:
    """Provider responds to a booking (accept / reject / complete)."""
    if data.status not in _PROVIDER_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status tidak valid",
        )
    profile = await provider_crud.get_profile_by_user(db, current_user.id)
    booking = await booking_crud.get_booking(db, booking_id)
    if booking is None or profile is None or booking.provider_id != profile.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pesanan tidak ditemukan"
        )
    return await booking_crud.set_status(db, booking, data.status)


@router.post("/{booking_id}/cancel", response_model=BookingRead)
async def cancel_booking(
    booking_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> BookingRead:
    """Resident cancels their own booking while it is still pending."""
    booking = await booking_crud.get_booking(db, booking_id)
    if booking is None or booking.customer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pesanan tidak ditemukan"
        )
    if booking.status != BookingStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hanya pesanan yang masih menunggu bisa dibatalkan",
        )
    return await booking_crud.set_status(db, booking, BookingStatus.CANCELLED)
