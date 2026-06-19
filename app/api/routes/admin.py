"""Administrator (pengelola) routes: verification and oversight."""

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel
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
from app.schemas.provider import ProviderProfileRead
from app.schemas.user import UserRead

router = APIRouter(prefix="/admin", tags=["admin"])


class AdminProviderRow(BaseModel):
    """Provider entry for the admin dashboard, with moderation info."""

    id: int
    user_id: int
    display_name: str
    profession: str
    is_verified: bool
    owner_active: bool
    service_count: int = 0
    rating_avg: float = 0.0
    rating_count: int = 0


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


@router.get("/providers", response_model=list[AdminProviderRow])
async def admin_list_providers(
    q: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> list[AdminProviderRow]:
    profiles = await provider_crud.list_profiles(db, q=q, limit=limit, offset=offset)
    return [
        AdminProviderRow(
            id=p.id,
            user_id=p.user_id,
            display_name=p.display_name,
            profession=p.profession,
            is_verified=p.is_verified,
            owner_active=bool(p.user and p.user.is_active),
            service_count=p.service_count,
            rating_avg=p.rating_avg,
            rating_count=p.rating_count,
        )
        for p in profiles
    ]


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


# --- Moderation --------------------------------------------------------------

async def _set_user_active(
    db: AsyncSession, admin: User, user_id: int, active: bool
) -> UserRead:
    user = await user_crud.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pengguna tidak ditemukan"
        )
    if user.role == UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tidak bisa menonaktifkan akun pengelola",
        )
    return await user_crud.set_user_active(db, user, active)


@router.post("/users/{user_id}/deactivate", response_model=UserRead)
async def admin_deactivate_user(
    user_id: int,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    return await _set_user_active(db, admin, user_id, False)


@router.post("/users/{user_id}/activate", response_model=UserRead)
async def admin_activate_user(
    user_id: int,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    return await _set_user_active(db, admin, user_id, True)


@router.delete("/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_review(
    review_id: int,
    _admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> Response:
    review = await provider_crud.get_review(db, review_id)
    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ulasan tidak ditemukan"
        )
    await provider_crud.delete_review(db, review)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
