from typing import Any

import pytest
from httpx import AsyncClient

_USER = {"email": "filter_chef@example.com", "password": "filterpassword"}

_RECIPES = [
    {
        "title": "Potato Stew",
        "instructions": "Peel and boil potatoes in a large oven dish",
        "servings": 4,
        "is_vegetarian": True,
        "ingredients": [{"name": "potatoes"}, {"name": "onion"}],
    },
    {
        "title": "Salmon Pasta",
        "instructions": "Cook pasta then pan-fry salmon",
        "servings": 2,
        "is_vegetarian": False,
        "ingredients": [{"name": "salmon"}, {"name": "pasta"}],
    },
    {
        "title": "Vegetable Soup",
        "instructions": "Chop vegetables and simmer on the hob",
        "servings": 4,
        "is_vegetarian": True,
        "ingredients": [{"name": "carrot"}, {"name": "celery"}],
    },
]


@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    await client.post("/api/v1/auth/register", json=_USER)
    r = await client.post("/api/v1/auth/login", json=_USER)
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
async def seeded(client: AsyncClient, auth_headers: dict[str, str]) -> list[dict[str, Any]]:
    created = []
    for recipe in _RECIPES:
        r = await client.post("/api/v1/recipes", json=recipe, headers=auth_headers)
        assert r.status_code == 201
        created.append(r.json())
    return created  # type: ignore[return-value]


# --- Spec example 1: all vegetarian ---


async def test_filter_vegetarian(
    client: AsyncClient, auth_headers: dict[str, str], seeded: list[dict[str, Any]]
) -> None:
    r = await client.get("/api/v1/recipes?is_vegetarian=true", headers=auth_headers)
    assert r.status_code == 200
    titles = {item["title"] for item in r.json()}
    assert titles == {"Potato Stew", "Vegetable Soup"}


# --- Spec example 2: servings=4 AND includes potatoes ---


async def test_filter_servings_and_include_ingredient(
    client: AsyncClient, auth_headers: dict[str, str], seeded: list[dict[str, Any]]
) -> None:
    r = await client.get(
        "/api/v1/recipes?servings=4&include_ingredients=potatoes",
        headers=auth_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["title"] == "Potato Stew"


# --- Spec example 3: exclude salmon AND instructions contain "oven" ---


async def test_filter_exclude_ingredient_and_instructions(
    client: AsyncClient, auth_headers: dict[str, str], seeded: list[dict[str, Any]]
) -> None:
    r = await client.get(
        "/api/v1/recipes?exclude_ingredients=salmon&instructions_contains=oven",
        headers=auth_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["title"] == "Potato Stew"


# --- Additional: combining multiple filters ---


async def test_no_results_when_no_match(
    client: AsyncClient, auth_headers: dict[str, str], seeded: list[dict[str, Any]]
) -> None:
    r = await client.get(
        "/api/v1/recipes?is_vegetarian=true&include_ingredients=salmon",
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert r.json() == []


async def test_pagination(
    client: AsyncClient, auth_headers: dict[str, str], seeded: list[dict[str, Any]]
) -> None:
    r = await client.get("/api/v1/recipes?page=1&page_size=2", headers=auth_headers)
    assert r.status_code == 200
    assert len(r.json()) == 2
