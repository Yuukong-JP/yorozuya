"""Tests for provider reviews (ulasan & penilaian)."""

import pytest
from httpx import AsyncClient

AUTH = "/api/v1/auth"
PROV = "/api/v1/providers"

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
async def provider_setup(client) -> tuple[int, str]:
    token = await _register_login(client, "budi_las", "budi@kolega.id", "provider")
    r = await client.post(f"{PROV}/me", json=PROFILE, headers=_h(token))
    return r.json()["id"], token


async def test_customer_can_review_and_average_updates(client, provider_setup):
    provider_id, _ = provider_setup
    c1 = await _register_login(client, "warga01", "w1@kolega.id", "customer")
    c2 = await _register_login(client, "warga02", "w2@kolega.id", "customer")

    r = await client.post(
        f"{PROV}/{provider_id}/reviews",
        json={"rating": 5, "comment": "Rapi sekali"},
        headers=_h(c1),
    )
    assert r.status_code == 201, r.text
    assert r.json()["author_username"] == "warga01"

    await client.post(
        f"{PROV}/{provider_id}/reviews", json={"rating": 4}, headers=_h(c2)
    )

    detail = (await client.get(f"{PROV}/{provider_id}")).json()
    assert detail["rating_count"] == 2
    assert detail["rating_avg"] == 4.5
    assert len(detail["reviews"]) == 2

    # Browse summary carries the aggregates too.
    summary = (await client.get(PROV)).json()[0]
    assert summary["rating_count"] == 2
    assert summary["rating_avg"] == 4.5


async def test_review_is_upserted_not_duplicated(client, provider_setup):
    provider_id, _ = provider_setup
    c1 = await _register_login(client, "warga01", "w1@kolega.id", "customer")

    await client.post(
        f"{PROV}/{provider_id}/reviews", json={"rating": 5}, headers=_h(c1)
    )
    await client.post(
        f"{PROV}/{provider_id}/reviews",
        json={"rating": 2, "comment": "Revisi"},
        headers=_h(c1),
    )
    detail = (await client.get(f"{PROV}/{provider_id}")).json()
    assert detail["rating_count"] == 1
    assert detail["rating_avg"] == 2.0


async def test_provider_cannot_review_self(client, provider_setup):
    provider_id, owner_token = provider_setup
    r = await client.post(
        f"{PROV}/{provider_id}/reviews", json={"rating": 5}, headers=_h(owner_token)
    )
    assert r.status_code == 403


async def test_anonymous_cannot_review(client, provider_setup):
    provider_id, _ = provider_setup
    r = await client.post(f"{PROV}/{provider_id}/reviews", json={"rating": 5})
    assert r.status_code == 401


async def test_rating_out_of_range_rejected(client, provider_setup):
    provider_id, _ = provider_setup
    c1 = await _register_login(client, "warga01", "w1@kolega.id", "customer")
    r = await client.post(
        f"{PROV}/{provider_id}/reviews", json={"rating": 9}, headers=_h(c1)
    )
    assert r.status_code == 422


async def test_review_unknown_provider_404(client):
    c1 = await _register_login(client, "warga01", "w1@kolega.id", "customer")
    r = await client.post(
        f"{PROV}/999/reviews", json={"rating": 5}, headers=_h(c1)
    )
    assert r.status_code == 404
