"""Tests for admin moderation (deactivate accounts, delete reviews)."""

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


async def _admin_token(client: AsyncClient, db_session) -> str:
    db_session.add(
        User(
            username="pengelola", email="admin@kolega.id",
            hashed_password=hash_password("password123"),
            role=UserRole.ADMIN.value, is_verified=True,
        )
    )
    await db_session.commit()
    r = await client.post(f"{AUTH}/login", data={"username": "pengelola", "password": "password123"})
    return r.json()["access_token"]


@pytest.fixture
async def provider(client):
    token = await _register_login(client, "budi_las", "budi@kolega.id", "provider")
    pid = (await client.post(f"{PROV}/me", json=PROFILE, headers=_h(token))).json()["id"]
    return {"token": token, "id": pid}


async def test_admin_deletes_review(client, db_session, provider):
    admin = await _admin_token(client, db_session)
    ctoken = await _register_login(client, "warga01", "w@kolega.id", "customer")
    rid = (
        await client.post(
            f"{PROV}/{provider['id']}/reviews",
            json={"rating": 1, "comment": "spam kasar"}, headers=_h(ctoken),
        )
    ).json()["id"]

    r = await client.delete(f"{ADMIN}/reviews/{rid}", headers=_h(admin))
    assert r.status_code == 204
    detail = (await client.get(f"{PROV}/{provider['id']}")).json()
    assert detail["rating_count"] == 0


async def test_admin_deactivates_account_blocks_login(client, db_session, provider):
    admin = await _admin_token(client, db_session)
    # find the provider's user_id via the admin listing
    rows = (await client.get(f"{ADMIN}/providers", headers=_h(admin))).json()
    uid = rows[0]["user_id"]
    assert rows[0]["owner_active"] is True

    r = await client.post(f"{ADMIN}/users/{uid}/deactivate", headers=_h(admin))
    assert r.status_code == 200 and r.json()["is_active"] is False

    # deactivated provider can no longer log in
    login = await client.post(
        f"{AUTH}/login", data={"username": "budi_las", "password": "password123"}
    )
    assert login.status_code == 400

    # reactivate restores access
    await client.post(f"{ADMIN}/users/{uid}/activate", headers=_h(admin))
    login = await client.post(
        f"{AUTH}/login", data={"username": "budi_las", "password": "password123"}
    )
    assert login.status_code == 200


async def test_admin_cannot_deactivate_admin(client, db_session, provider):
    admin = await _admin_token(client, db_session)
    me = (await client.get(f"{AUTH}/me", headers=_h(admin))).json()
    r = await client.post(f"{ADMIN}/users/{me['id']}/deactivate", headers=_h(admin))
    assert r.status_code == 403


async def test_non_admin_cannot_moderate(client, provider):
    customer = await _register_login(client, "warga01", "w@kolega.id", "customer")
    assert (await client.delete(f"{ADMIN}/reviews/1", headers=_h(customer))).status_code == 403
    assert (await client.post(f"{ADMIN}/users/1/deactivate", headers=_h(customer))).status_code == 403
