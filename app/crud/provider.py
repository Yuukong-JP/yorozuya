"""Database operations for provider profiles and their services."""

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import ServiceCategory
from app.models.provider import ProviderProfile, Service
from app.schemas.provider import ProviderProfileCreate, ProviderProfileUpdate
from app.schemas.service import ServiceCreate, ServiceUpdate


# --- Provider profiles -------------------------------------------------------

async def get_profile_by_id(
    db: AsyncSession, provider_id: int
) -> ProviderProfile | None:
    result = await db.execute(
        select(ProviderProfile)
        .where(ProviderProfile.id == provider_id)
        .options(selectinload(ProviderProfile.services))
    )
    return result.scalar_one_or_none()


async def get_profile_by_user(
    db: AsyncSession, user_id: int
) -> ProviderProfile | None:
    result = await db.execute(
        select(ProviderProfile)
        .where(ProviderProfile.user_id == user_id)
        .options(selectinload(ProviderProfile.services))
    )
    return result.scalar_one_or_none()


async def create_profile(
    db: AsyncSession, user_id: int, data: ProviderProfileCreate
) -> ProviderProfile:
    profile = ProviderProfile(user_id=user_id, **data.model_dump())
    db.add(profile)
    await db.commit()
    return await get_profile_by_id(db, profile.id)


async def update_profile(
    db: AsyncSession, profile: ProviderProfile, data: ProviderProfileUpdate
) -> ProviderProfile:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    await db.commit()
    return await get_profile_by_id(db, profile.id)


async def list_profiles(
    db: AsyncSession,
    q: str | None = None,
    category: ServiceCategory | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[ProviderProfile]:
    stmt = select(ProviderProfile).options(
        selectinload(ProviderProfile.services)
    )
    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(
            or_(
                ProviderProfile.display_name.ilike(pattern),
                ProviderProfile.profession.ilike(pattern),
                ProviderProfile.headline.ilike(pattern),
            )
        )
    if category is not None:
        stmt = stmt.where(
            ProviderProfile.id.in_(
                select(Service.provider_id).where(
                    Service.category == category.value,
                    Service.is_active.is_(True),
                )
            )
        )
    stmt = (
        stmt.order_by(ProviderProfile.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    profiles = list(result.scalars().all())
    # Attach lightweight aggregates used by browse cards.
    for profile in profiles:
        active = [s for s in profile.services if s.is_active]
        profile.service_count = len(active)
        if active:
            cheapest = min(active, key=lambda s: s.price)
            profile.starting_price = cheapest.price
            profile.primary_category = cheapest.category
        else:
            profile.starting_price = None
            profile.primary_category = None
    return profiles


# --- Services ----------------------------------------------------------------

async def create_service(
    db: AsyncSession, provider_id: int, data: ServiceCreate
) -> Service:
    payload = data.model_dump()
    payload["category"] = data.category.value
    service = Service(provider_id=provider_id, **payload)
    db.add(service)
    await db.commit()
    await db.refresh(service)
    return service


async def get_service(db: AsyncSession, service_id: int) -> Service | None:
    return await db.get(Service, service_id)


async def list_services(db: AsyncSession, provider_id: int) -> list[Service]:
    result = await db.execute(
        select(Service)
        .where(Service.provider_id == provider_id)
        .order_by(Service.created_at.desc())
    )
    return list(result.scalars().all())


async def update_service(
    db: AsyncSession, service: Service, data: ServiceUpdate
) -> Service:
    payload = data.model_dump(exclude_unset=True)
    if "category" in payload and payload["category"] is not None:
        payload["category"] = data.category.value
    for field, value in payload.items():
        setattr(service, field, value)
    await db.commit()
    await db.refresh(service)
    return service


async def delete_service(db: AsyncSession, service: Service) -> None:
    await db.delete(service)
    await db.commit()
