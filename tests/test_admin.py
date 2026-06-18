"""Tests for administrator (pengelola) verification and oversight."""

import pytest
from httpx import AsyncClient

from app.core.security import hash_password
from app.models.enums import UserRole
from app.models.user import User

AUTH = "/api/v1/auth"
PROV = "/api/v1/providers"
ADMIN = "/api/v1/admin"

PROFILE = {"display_name": "Budi Las Jaya", "profession": "Tukang Las"}


async def _register_login(client: AsyncClient, username, email, role) -> str:
    await client.post(
        f"{AUTH}/register",
        json={"username": username, "email": email, "password": "password123", "role": role},
    )
    r = await client.post(
        f"{AUTH}/login", data={"username": username, "password": "password123"}
    )
    return r.json()["access_token"]


def _h(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _make_admin_token(client: AsyncClient, db_session) -> str:
    db_session.add(
        User(
            username="pengelola",
            email="admin@kolega.id",
            hashed_password=hash_password("password123"),
            role=UserRole.ADMIN.value,
            is_verified=True,
        )
    )
    await db_session.commit()
    r = await client.post(
        f"{AUTH}/login", data={"username": "pengelola", "password": "password123"}
    )
    return r.json()["access_token"]


@pytest.fixture
async def provider_id(client) -> int:
    token = await _register_login(client, "budi_las", "budi@kolega.id", "provider")
    r = await client.post(f"{PROV}/me", json=PROFILE, headers=_h(token))
    return r.json()["id"]


async def test_admin_can_verify_and_unverify(client, db_session, provider_id):
    admin = await _make_admin_token(client, db_session)

    detail = (await client.get(f"{PROV}/{provider_id}")).json()
    assert detail["is_verified"] is False

    r = await client.post(f"{ADMIN}/providers/{provider_id}/verify", headers=_h(admin))
    assert r.status_code == 200, r.text
    assert r.json()["is_verified"] is True

    detail = (await client.get(f"{PROV}/{provider_id}")).json()
    assert detail["is_verified"] is True

    r = await client.post(f"{ADMIN}/providers/{provider_id}/unverify", headers=_h(admin))
    assert r.json()["is_verified"] is False


async def test_admin_stats(client, db_session, provider_id):
    admin = await _make_admin_token(client, db_session)
    await client.post(f"{ADMIN}/providers/{provider_id}/verify", headers=_h(admin))
    stats = (await client.get(f"{ADMIN}/stats", headers=_h(admin))).json()
    assert stats["providers"] == 1
    assert stats["verified_providers"] == 1
    assert stats["pending_providers"] == 0


async def test_non_admin_blocked(client, provider_id):
    customer = await _register_login(client, "warga01", "w@kolega.id", "customer")
    r = await client.get(f"{ADMIN}/providers", headers=_h(customer))
    assert r.status_code == 403
    r = await client.post(f"{ADMIN}/providers/{provider_id}/verify", headers=_h(customer))
    assert r.status_code == 403


async def test_admin_endpoints_require_auth(client):
    assert (await client.get(f"{ADMIN}/stats")).status_code == 401
