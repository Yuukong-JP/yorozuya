"""Tests for the registration / login / current-user flow."""

import pytest
from httpx import AsyncClient

PREFIX = "/api/v1/auth"


async def register(client: AsyncClient, payload: dict[str, str]):
    return await client.post(f"{PREFIX}/register", json=payload)


async def login(client: AsyncClient, username: str, password: str):
    return await client.post(
        f"{PREFIX}/login", data={"username": username, "password": password}
    )


async def test_register_returns_created_user(client, user_payload):
    resp = await register(client, user_payload)
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == user_payload["email"]
    assert body["username"] == user_payload["username"]
    assert body["is_active"] is True
    assert body["is_superuser"] is False
    assert "id" in body
    # The password must never be exposed.
    assert "password" not in body
    assert "hashed_password" not in body


async def test_register_duplicate_email_conflicts(client, user_payload):
    await register(client, user_payload)
    dup = dict(user_payload, username="otose")
    resp = await register(client, dup)
    assert resp.status_code == 409


async def test_register_duplicate_username_conflicts(client, user_payload):
    await register(client, user_payload)
    dup = dict(user_payload, email="other@yorozuya.jp")
    resp = await register(client, dup)
    assert resp.status_code == 409


@pytest.mark.parametrize(
    "payload",
    [
        {"email": "not-an-email", "username": "kagura", "password": "longenough1"},
        {"email": "kagura@yorozuya.jp", "username": "ka", "password": "longenough1"},
        {"email": "kagura@yorozuya.jp", "username": "kagura", "password": "short"},
    ],
)
async def test_register_validation_errors(client, payload):
    resp = await register(client, payload)
    assert resp.status_code == 422


async def test_login_returns_token(client, user_payload):
    await register(client, user_payload)
    resp = await login(client, user_payload["username"], user_payload["password"])
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


async def test_login_wrong_password_unauthorized(client, user_payload):
    await register(client, user_payload)
    resp = await login(client, user_payload["username"], "wrong-password")
    assert resp.status_code == 401


async def test_login_unknown_user_unauthorized(client):
    resp = await login(client, "nobody", "whatever123")
    assert resp.status_code == 401


async def test_me_with_valid_token(client, user_payload):
    await register(client, user_payload)
    token = (
        await login(client, user_payload["username"], user_payload["password"])
    ).json()["access_token"]
    resp = await client.get(
        f"{PREFIX}/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["username"] == user_payload["username"]


async def test_me_without_token_unauthorized(client):
    resp = await client.get(f"{PREFIX}/me")
    assert resp.status_code == 401


async def test_me_with_invalid_token_unauthorized(client):
    resp = await client.get(
        f"{PREFIX}/me", headers={"Authorization": "Bearer not.a.real.token"}
    )
    assert resp.status_code == 401
