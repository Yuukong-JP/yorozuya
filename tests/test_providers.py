"""Tests for provider profiles and services."""

import pytest
from httpx import AsyncClient

AUTH = "/api/v1/auth"
PROV = "/api/v1/providers"


async def _register_login(client: AsyncClient, username, email, role) -> str:
    await client.post(
        f"{AUTH}/register",
        json={
            "username": username,
            "email": email,
            "password": "password123",
            "role": role,
        },
    )
    r = await client.post(
        f"{AUTH}/login", data={"username": username, "password": "password123"}
    )
    return r.json()["access_token"]


def _h(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def provider_token(client) -> str:
    return await _register_login(client, "budi_las", "budi@kolega.id", "provider")


@pytest.fixture
async def customer_token(client) -> str:
    return await _register_login(client, "warga01", "warga@kolega.id", "customer")


PROFILE = {
    "display_name": "Budi Las Jaya",
    "profession": "Tukang Las",
    "headline": "Las pagar, teralis, kanopi",
    "city": "Padang Panjang",
}
SERVICE = {
    "title": "Pembuatan pagar besi",
    "description": "Termasuk pengukuran dan pemasangan",
    "category": "tukang_las",
    "price": 350000,
    "price_unit": "per meter",
}


# --- Profile -----------------------------------------------------------------

async def test_provider_creates_profile(client, provider_token):
    r = await client.post(f"{PROV}/me", json=PROFILE, headers=_h(provider_token))
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["display_name"] == "Budi Las Jaya"
    assert body["is_verified"] is False
    assert body["services"] == []


async def test_duplicate_profile_conflicts(client, provider_token):
    await client.post(f"{PROV}/me", json=PROFILE, headers=_h(provider_token))
    r = await client.post(f"{PROV}/me", json=PROFILE, headers=_h(provider_token))
    assert r.status_code == 409


async def test_customer_cannot_create_profile(client, customer_token):
    r = await client.post(f"{PROV}/me", json=PROFILE, headers=_h(customer_token))
    assert r.status_code == 403


async def test_get_my_profile_before_creation_is_404(client, provider_token):
    r = await client.get(f"{PROV}/me", headers=_h(provider_token))
    assert r.status_code == 404


async def test_update_my_profile(client, provider_token):
    await client.post(f"{PROV}/me", json=PROFILE, headers=_h(provider_token))
    r = await client.patch(
        f"{PROV}/me", json={"headline": "Spesialis kanopi"}, headers=_h(provider_token)
    )
    assert r.status_code == 200
    assert r.json()["headline"] == "Spesialis kanopi"
    assert r.json()["profession"] == "Tukang Las"  # unchanged


async def test_unauthenticated_cannot_access_me(client):
    assert (await client.get(f"{PROV}/me")).status_code == 401


# --- Services ----------------------------------------------------------------

async def test_add_service_requires_profile(client, provider_token):
    r = await client.post(
        f"{PROV}/me/services", json=SERVICE, headers=_h(provider_token)
    )
    assert r.status_code == 404


async def test_add_and_list_services(client, provider_token):
    await client.post(f"{PROV}/me", json=PROFILE, headers=_h(provider_token))
    r = await client.post(
        f"{PROV}/me/services", json=SERVICE, headers=_h(provider_token)
    )
    assert r.status_code == 201, r.text
    assert r.json()["category"] == "tukang_las"
    assert r.json()["price"] == 350000

    lst = await client.get(f"{PROV}/me/services", headers=_h(provider_token))
    assert lst.status_code == 200
    assert len(lst.json()) == 1


async def test_invalid_category_rejected(client, provider_token):
    await client.post(f"{PROV}/me", json=PROFILE, headers=_h(provider_token))
    bad = dict(SERVICE, category="tidak_ada")
    r = await client.post(f"{PROV}/me/services", json=bad, headers=_h(provider_token))
    assert r.status_code == 422


async def test_update_and_delete_service(client, provider_token):
    await client.post(f"{PROV}/me", json=PROFILE, headers=_h(provider_token))
    created = await client.post(
        f"{PROV}/me/services", json=SERVICE, headers=_h(provider_token)
    )
    sid = created.json()["id"]

    upd = await client.patch(
        f"{PROV}/me/services/{sid}", json={"price": 400000}, headers=_h(provider_token)
    )
    assert upd.status_code == 200
    assert upd.json()["price"] == 400000

    dele = await client.delete(
        f"{PROV}/me/services/{sid}", headers=_h(provider_token)
    )
    assert dele.status_code == 204
    lst = await client.get(f"{PROV}/me/services", headers=_h(provider_token))
    assert lst.json() == []


async def test_cannot_touch_other_providers_service(client, provider_token):
    # Provider A creates a profile + service
    await client.post(f"{PROV}/me", json=PROFILE, headers=_h(provider_token))
    created = await client.post(
        f"{PROV}/me/services", json=SERVICE, headers=_h(provider_token)
    )
    sid = created.json()["id"]

    # Provider B
    other = await _register_login(client, "siti_jahit", "siti@kolega.id", "provider")
    await client.post(
        f"{PROV}/me",
        json={"display_name": "Siti Jahit", "profession": "Penjahit"},
        headers=_h(other),
    )
    r = await client.patch(
        f"{PROV}/me/services/{sid}", json={"price": 1}, headers=_h(other)
    )
    assert r.status_code == 404


# --- Public browse -----------------------------------------------------------

async def test_browse_and_filter(client, provider_token):
    await client.post(f"{PROV}/me", json=PROFILE, headers=_h(provider_token))
    await client.post(
        f"{PROV}/me/services", json=SERVICE, headers=_h(provider_token)
    )

    # Browse (public, no auth)
    r = await client.get(PROV)
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["display_name"] == "Budi Las Jaya"

    # Search query
    assert len(((await client.get(f"{PROV}?q=las")).json())) == 1
    assert len(((await client.get(f"{PROV}?q=fotografi")).json())) == 0

    # Category filter
    assert len(((await client.get(f"{PROV}?category=tukang_las")).json())) == 1
    assert len(((await client.get(f"{PROV}?category=jahit")).json())) == 0


async def test_public_provider_detail(client, provider_token):
    profile = await client.post(
        f"{PROV}/me", json=PROFILE, headers=_h(provider_token)
    )
    pid = profile.json()["id"]
    await client.post(
        f"{PROV}/me/services", json=SERVICE, headers=_h(provider_token)
    )

    r = await client.get(f"{PROV}/{pid}")
    assert r.status_code == 200
    assert r.json()["display_name"] == "Budi Las Jaya"
    assert len(r.json()["services"]) == 1


async def test_public_detail_not_found(client):
    assert (await client.get(f"{PROV}/9999")).status_code == 404
