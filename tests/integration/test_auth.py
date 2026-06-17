from typing import Any

import pytest
from httpx import AsyncClient

_USER = {"email": "alice@example.com", "password": "hunter2hunter"}


@pytest.fixture
async def registered(client: AsyncClient) -> dict[str, Any]:
    r = await client.post("/api/v1/auth/register", json=_USER)
    assert r.status_code == 201
    return r.json()  # type: ignore[no-any-return]


@pytest.fixture
async def tokens(client: AsyncClient, registered: dict[str, Any]) -> dict[str, Any]:
    r = await client.post("/api/v1/auth/login", json=_USER)
    assert r.status_code == 200
    return r.json()  # type: ignore[no-any-return]


async def test_register_returns_user(client: AsyncClient) -> None:
    r = await client.post("/api/v1/auth/register", json=_USER)
    assert r.status_code == 201
    data = r.json()
    assert data["email"] == _USER["email"]
    assert "id" in data
    assert "password" not in data


async def test_register_duplicate_returns_409(
    client: AsyncClient, registered: dict[str, Any]
) -> None:
    r = await client.post("/api/v1/auth/register", json=_USER)
    assert r.status_code == 409


async def test_login_returns_tokens(client: AsyncClient, registered: dict[str, Any]) -> None:
    r = await client.post("/api/v1/auth/login", json=_USER)
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


async def test_login_wrong_password_returns_401(
    client: AsyncClient, registered: dict[str, Any]
) -> None:
    r = await client.post("/api/v1/auth/login", json={**_USER, "password": "wrong"})
    assert r.status_code == 401


async def test_refresh_rotates_tokens(client: AsyncClient, tokens: dict[str, Any]) -> None:
    r = await client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 200
    new = r.json()
    assert "access_token" in new
    assert "refresh_token" in new
    assert new["token_type"] == "bearer"


async def test_refresh_reuse_returns_401(client: AsyncClient, tokens: dict[str, Any]) -> None:
    await client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    r = await client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 401


async def test_logout_blocks_refresh(client: AsyncClient, tokens: dict[str, Any]) -> None:
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    r = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
        headers=headers,
    )
    assert r.status_code == 204
    r = await client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 401
