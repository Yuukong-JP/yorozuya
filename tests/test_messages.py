"""Tests for booking chat messages (obrolan pesanan)."""

import pytest
from httpx import AsyncClient

AUTH = "/api/v1/auth"
PROV = "/api/v1/providers"
BOOK = "/api/v1/bookings"

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


@pytest.fixture
async def setup(client):
    ptoken = await _register_login(client, "budi_las", "budi@kolega.id", "provider")
    pid = (await client.post(f"{PROV}/me", json=PROFILE, headers=_h(ptoken))).json()["id"]
    ctoken = await _register_login(client, "warga01", "w@kolega.id", "customer")
    bid = (
        await client.post(BOOK, json={"provider_id": pid}, headers=_h(ctoken))
    ).json()["id"]
    return {"ptoken": ptoken, "ctoken": ctoken, "bid": bid, "pid": pid}


async def test_chat_between_participants(client, setup):
    # customer sends
    r = await client.post(
        f"{BOOK}/{setup['bid']}/messages",
        json={"body": "Halo pak, bisa dikerjakan minggu ini?"},
        headers=_h(setup["ctoken"]),
    )
    assert r.status_code == 201, r.text
    assert r.json()["sender_username"] == "warga01"

    # provider replies
    await client.post(
        f"{BOOK}/{setup['bid']}/messages",
        json={"body": "Bisa, Sabtu ya."},
        headers=_h(setup["ptoken"]),
    )

    # both see the full thread in order
    msgs = (await client.get(f"{BOOK}/{setup['bid']}/messages", headers=_h(setup["ptoken"]))).json()
    assert [m["body"] for m in msgs] == [
        "Halo pak, bisa dikerjakan minggu ini?",
        "Bisa, Sabtu ya.",
    ]


async def test_outsider_cannot_access_chat(client, setup):
    other = await _register_login(client, "orang_lain", "x@kolega.id", "customer")
    assert (await client.get(f"{BOOK}/{setup['bid']}/messages", headers=_h(other))).status_code == 403
    assert (
        await client.post(
            f"{BOOK}/{setup['bid']}/messages", json={"body": "intip"}, headers=_h(other)
        )
    ).status_code == 403


async def test_chat_requires_auth(client, setup):
    assert (await client.get(f"{BOOK}/{setup['bid']}/messages")).status_code == 401


async def test_empty_message_rejected(client, setup):
    r = await client.post(
        f"{BOOK}/{setup['bid']}/messages", json={"body": ""}, headers=_h(setup["ctoken"])
    )
    assert r.status_code == 422
