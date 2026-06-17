import uuid
from typing import Any

import pytest
from httpx import AsyncClient

_USER = {"email": "chef@example.com", "password": "cookingpassword"}
_OTHER = {"email": "other@example.com", "password": "otherpassword"}
_RECIPE = {
    "title": "Margherita Pizza",
    "instructions": "Make dough, add sauce, bake",
    "servings": 2,
    "is_vegetarian": True,
    "ingredients": [
        {"name": "flour", "quantity": "500", "unit": "g"},
        {"name": "tomato sauce", "quantity": "200", "unit": "ml"},
    ],
}


@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    await client.post("/api/v1/auth/register", json=_USER)
    r = await client.post("/api/v1/auth/login", json=_USER)
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
async def other_headers(client: AsyncClient) -> dict[str, str]:
    await client.post("/api/v1/auth/register", json=_OTHER)
    r = await client.post("/api/v1/auth/login", json=_OTHER)
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
async def recipe(client: AsyncClient, auth_headers: dict[str, str]) -> dict[str, Any]:
    r = await client.post("/api/v1/recipes", json=_RECIPE, headers=auth_headers)
    assert r.status_code == 201
    return r.json()  # type: ignore[no-any-return]


async def test_create_recipe(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    r = await client.post("/api/v1/recipes", json=_RECIPE, headers=auth_headers)
    assert r.status_code == 201
    data = r.json()
    assert data["title"] == _RECIPE["title"]
    assert data["is_vegetarian"] is True
    assert len(data["ingredients"]) == 2
    assert "id" in data


async def test_get_recipe(
    client: AsyncClient, auth_headers: dict[str, str], recipe: dict[str, Any]
) -> None:
    r = await client.get(f"/api/v1/recipes/{recipe['id']}", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["title"] == _RECIPE["title"]


async def test_list_recipes(
    client: AsyncClient, auth_headers: dict[str, str], recipe: dict[str, Any]
) -> None:
    r = await client.get("/api/v1/recipes", headers=auth_headers)
    assert r.status_code == 200
    assert len(r.json()) == 1


async def test_update_recipe(
    client: AsyncClient, auth_headers: dict[str, str], recipe: dict[str, Any]
) -> None:
    r = await client.patch(
        f"/api/v1/recipes/{recipe['id']}",
        json={"title": "Updated Pizza", "servings": 4},
        headers=auth_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["title"] == "Updated Pizza"
    assert data["servings"] == 4
    assert data["is_vegetarian"] is True


async def test_delete_recipe(
    client: AsyncClient, auth_headers: dict[str, str], recipe: dict[str, Any]
) -> None:
    r = await client.delete(f"/api/v1/recipes/{recipe['id']}", headers=auth_headers)
    assert r.status_code == 204
    r = await client.get(f"/api/v1/recipes/{recipe['id']}", headers=auth_headers)
    assert r.status_code == 404


async def test_get_nonexistent_returns_404(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    r = await client.get(f"/api/v1/recipes/{uuid.uuid4()}", headers=auth_headers)
    assert r.status_code == 404


async def test_other_user_cannot_read_recipe(
    client: AsyncClient, recipe: dict[str, Any], other_headers: dict[str, str]
) -> None:
    r = await client.get(f"/api/v1/recipes/{recipe['id']}", headers=other_headers)
    assert r.status_code == 404


async def test_other_user_cannot_delete_recipe(
    client: AsyncClient, recipe: dict[str, Any], other_headers: dict[str, str]
) -> None:
    r = await client.delete(f"/api/v1/recipes/{recipe['id']}", headers=other_headers)
    assert r.status_code == 404


async def test_create_recipe_requires_auth(client: AsyncClient) -> None:
    r = await client.post("/api/v1/recipes", json=_RECIPE)
    assert r.status_code == 401
