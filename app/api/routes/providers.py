"""Provider profile and service routes (penyedia & paket layanan)."""

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_current_provider
from app.core.database import get_db
from app.crud import provider as provider_crud
from app.models.enums import ServiceCategory
from app.models.user import User
from app.schemas.provider import (
    ProviderProfileCreate,
    ProviderProfileRead,
    ProviderProfileUpdate,
    ProviderSummary,
)
from app.schemas.review import ReviewCreate, ReviewRead
from app.schemas.service import ServiceCreate, ServiceRead, ServiceUpdate

router = APIRouter(prefix="/providers", tags=["providers"])


# --- My profile (provider only) ----------------------------------------------

@router.post(
    "/me",
    response_model=ProviderProfileRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_my_profile(
    data: ProviderProfileCreate,
    current_user: User = Depends(get_current_provider),
    db: AsyncSession = Depends(get_db),
) -> ProviderProfileRead:
    if await provider_crud.get_profile_by_user(db, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Profil penyedia sudah ada",
        )
    return await provider_crud.create_profile(db, current_user.id, data)


@router.get("/me", response_model=ProviderProfileRead)
async def read_my_profile(
    current_user: User = Depends(get_current_provider),
    db: AsyncSession = Depends(get_db),
) -> ProviderProfileRead:
    profile = await provider_crud.get_profile_by_user(db, current_user.id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil penyedia belum dibuat",
        )
    return profile


@router.patch("/me", response_model=ProviderProfileRead)
async def update_my_profile(
    data: ProviderProfileUpdate,
    current_user: User = Depends(get_current_provider),
    db: AsyncSession = Depends(get_db),
) -> ProviderProfileRead:
    profile = await provider_crud.get_profile_by_user(db, current_user.id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil penyedia belum dibuat",
        )
    return await provider_crud.update_profile(db, profile, data)


# --- My services (provider only) ---------------------------------------------

async def _require_my_profile(current_user: User, db: AsyncSession):
    profile = await provider_crud.get_profile_by_user(db, current_user.id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Buat profil penyedia terlebih dahulu",
        )
    return profile


@router.post(
    "/me/services",
    response_model=ServiceRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_my_service(
    data: ServiceCreate,
    current_user: User = Depends(get_current_provider),
    db: AsyncSession = Depends(get_db),
) -> ServiceRead:
    profile = await _require_my_profile(current_user, db)
    return await provider_crud.create_service(db, profile.id, data)


@router.get("/me/services", response_model=list[ServiceRead])
async def list_my_services(
    current_user: User = Depends(get_current_provider),
    db: AsyncSession = Depends(get_db),
) -> list[ServiceRead]:
    profile = await _require_my_profile(current_user, db)
    return await provider_crud.list_services(db, profile.id)


@router.patch("/me/services/{service_id}", response_model=ServiceRead)
async def update_my_service(
    service_id: int,
    data: ServiceUpdate,
    current_user: User = Depends(get_current_provider),
    db: AsyncSession = Depends(get_db),
) -> ServiceRead:
    profile = await _require_my_profile(current_user, db)
    service = await provider_crud.get_service(db, service_id)
    if service is None or service.provider_id != profile.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Layanan tidak ditemukan"
        )
    return await provider_crud.update_service(db, service, data)


@router.delete("/me/services/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_service(
    service_id: int,
    current_user: User = Depends(get_current_provider),
    db: AsyncSession = Depends(get_db),
) -> Response:
    profile = await _require_my_profile(current_user, db)
    service = await provider_crud.get_service(db, service_id)
    if service is None or service.provider_id != profile.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Layanan tidak ditemukan"
        )
    await provider_crud.delete_service(db, service)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Public browse -----------------------------------------------------------

@router.get("", response_model=list[ProviderSummary])
async def browse_providers(
    q: str | None = Query(default=None, description="Cari nama/keahlian"),
    category: ServiceCategory | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> list[ProviderSummary]:
    return await provider_crud.list_profiles(
        db, q=q, category=category, limit=limit, offset=offset
    )


@router.get("/{provider_id}", response_model=ProviderProfileRead)
async def read_provider(
    provider_id: int,
    db: AsyncSession = Depends(get_db),
) -> ProviderProfileRead:
    profile = await provider_crud.get_profile_by_id(db, provider_id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Penyedia tidak ditemukan"
        )
    return profile


# --- Reviews -----------------------------------------------------------------

@router.get("/{provider_id}/reviews", response_model=list[ReviewRead])
async def list_provider_reviews(
    provider_id: int,
    db: AsyncSession = Depends(get_db),
) -> list[ReviewRead]:
    if await provider_crud.get_profile_by_id(db, provider_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Penyedia tidak ditemukan"
        )
    return await provider_crud.list_reviews(db, provider_id)


@router.post(
    "/{provider_id}/reviews",
    response_model=ReviewRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_provider_review(
    provider_id: int,
    data: ReviewCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ReviewRead:
    profile = await provider_crud.get_profile_by_id(db, provider_id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Penyedia tidak ditemukan"
        )
    if profile.user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tidak bisa menilai diri sendiri",
        )
    return await provider_crud.create_or_update_review(
        db, provider_id, current_user.id, data
    )
