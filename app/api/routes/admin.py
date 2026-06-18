"""Administrator (pengelola) routes: verification and oversight."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.core.database import get_db
from app.crud import provider as provider_crud
from app.crud import user as user_crud
from app.models.booking import Booking
from app.models.enums import UserRole
from app.models.provider import ProviderProfile, Review
from app.models.user import User
from app.schemas.provider import ProviderProfileRead, ProviderSummary

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats")
async def admin_stats(
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, int]:
    async def _count(stmt) -> int:
        return int((await db.execute(stmt)).scalar_one())

    providers = await _count(select(func.count()).select_from(ProviderProfile))
    verified = await _count(
        select(func.count()).select_from(User).where(
            User.role == UserRole.PROVIDER.value, User.is_verified.is_(True)
        )
    )
    customers = await _count(
        select(func.count()).select_from(User).where(
            User.role == UserRole.CUSTOMER.value
        )
    )
    reviews = await _count(select(func.count()).select_from(Review))
    bookings = await _count(select(func.count()).select_from(Booking))
    return {
        "providers": providers,
        "verified_providers": verified,
        "pending_providers": providers - verified,
        "customers": customers,
        "reviews": reviews,
        "bookings": bookings,
    }


@router.get("/providers", response_model=list[ProviderSummary])
async def admin_list_providers(
    q: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> list[ProviderSummary]:
    return await provider_crud.list_profiles(db, q=q, limit=limit, offset=offset)


async def _set_verification(
    db: AsyncSession, provider_id: int, verified: bool
) -> ProviderProfileRead:
    profile = await provider_crud.get_profile_by_id(db, provider_id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Penyedia tidak ditemukan"
        )
    owner = await user_crud.get_user_by_id(db, profile.user_id)
    await user_crud.set_user_verified(db, owner, verified)
    return await provider_crud.get_profile_by_id(db, provider_id)


@router.post("/providers/{provider_id}/verify", response_model=ProviderProfileRead)
async def admin_verify_provider(
    provider_id: int,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> ProviderProfileRead:
    return await _set_verification(db, provider_id, True)


@router.post(
    "/providers/{provider_id}/unverify", response_model=ProviderProfileRead
)
async def admin_unverify_provider(
    provider_id: int,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> ProviderProfileRead:
    return await _set_verification(db, provider_id, False)
