"""Tests for bookings (pemesanan layanan)."""

import pytest
from httpx import AsyncClient

AUTH = "/api/v1/auth"
PROV = "/api/v1/providers"
BOOK = "/api/v1/bookings"

PROFILE = {"display_name": "Budi Las Jaya", "profession": "Tukang Las"}
SERVICE = {"title": "Pagar besi", "category": "tukang_las", "price": 350000}


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


@pytest.fixture
async def setup(client):
    ptoken = await _register_login(client, "budi_las", "budi@kolega.id", "provider")
    pid = (await client.post(f"{PROV}/me", json=PROFILE, headers=_h(ptoken))).json()["id"]
    sid = (
        await client.post(f"{PROV}/me/services", json=SERVICE, headers=_h(ptoken))
    ).json()["id"]
    ctoken = await _register_login(client, "warga01", "w@kolega.id", "customer")
    return {"ptoken": ptoken, "pid": pid, "sid": sid, "ctoken": ctoken}


async def test_full_booking_flow(client, setup):
    # customer books a specific service
    r = await client.post(
        BOOK,
        json={"provider_id": setup["pid"], "service_id": setup["sid"],
              "note": "Tolong buatkan pagar 5 meter", "preferred_time": "Sabtu pagi"},
        headers=_h(setup["ctoken"]),
    )
    assert r.status_code == 201, r.text
    b = r.json()
    assert b["status"] == "pending"
    assert b["provider_name"] == "Budi Las Jaya"
    assert b["service_title"] == "Pagar besi"
    bid = b["id"]

    # appears in customer's list
    mine = (await client.get(f"{BOOK}/me", headers=_h(setup["ctoken"]))).json()
    assert len(mine) == 1

    # appears in provider's incoming list
    incoming = (await client.get(f"{BOOK}/incoming", headers=_h(setup["ptoken"]))).json()
    assert len(incoming) == 1 and incoming[0]["id"] == bid

    # provider accepts
    r = await client.post(
        f"{BOOK}/{bid}/status", json={"status": "accepted"}, headers=_h(setup["ptoken"])
    )
    assert r.status_code == 200 and r.json()["status"] == "accepted"

    # provider completes
    r = await client.post(
        f"{BOOK}/{bid}/status", json={"status": "completed"}, headers=_h(setup["ptoken"])
    )
    assert r.json()["status"] == "completed"


async def test_customer_can_cancel_pending(client, setup):
    bid = (
        await client.post(
            BOOK, json={"provider_id": setup["pid"]}, headers=_h(setup["ctoken"])
        )
    ).json()["id"]
    r = await client.post(f"{BOOK}/{bid}/cancel", headers=_h(setup["ctoken"]))
    assert r.status_code == 200 and r.json()["status"] == "cancelled"


async def test_cannot_cancel_after_accepted(client, setup):
    bid = (
        await client.post(
            BOOK, json={"provider_id": setup["pid"]}, headers=_h(setup["ctoken"])
        )
    ).json()["id"]
    await client.post(
        f"{BOOK}/{bid}/status", json={"status": "accepted"}, headers=_h(setup["ptoken"])
    )
    r = await client.post(f"{BOOK}/{bid}/cancel", headers=_h(setup["ctoken"]))
    assert r.status_code == 400


async def test_provider_cannot_book_self(client, setup):
    r = await client.post(
        BOOK, json={"provider_id": setup["pid"]}, headers=_h(setup["ptoken"])
    )
    assert r.status_code == 403


async def test_provider_status_must_be_valid(client, setup):
    bid = (
        await client.post(
            BOOK, json={"provider_id": setup["pid"]}, headers=_h(setup["ctoken"])
        )
    ).json()["id"]
    r = await client.post(
        f"{BOOK}/{bid}/status", json={"status": "pending"}, headers=_h(setup["ptoken"])
    )
    assert r.status_code == 400


async def test_booking_requires_auth(client, setup):
    r = await client.post(BOOK, json={"provider_id": setup["pid"]})
    assert r.status_code == 401


async def test_service_must_belong_to_provider(client, setup):
    r = await client.post(
        BOOK,
        json={"provider_id": setup["pid"], "service_id": 9999},
        headers=_h(setup["ctoken"]),
    )
    assert r.status_code == 404
