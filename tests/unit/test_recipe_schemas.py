import pytest
from pydantic import ValidationError

from app.schemas.recipe import IngredientIn, RecipeCreateRequest, RecipeUpdateRequest


def test_recipe_create_defaults():
    r = RecipeCreateRequest(title="Pasta", instructions="Boil pasta", servings=4)
    assert r.is_vegetarian is False
    assert r.ingredients == []
    assert r.description is None


def test_recipe_create_with_ingredients():
    r = RecipeCreateRequest(
        title="Salad",
        instructions="Mix everything",
        servings=2,
        is_vegetarian=True,
        ingredients=[IngredientIn(name="lettuce", quantity="100", unit="g")],
    )
    assert len(r.ingredients) == 1
    assert r.ingredients[0].name == "lettuce"


def test_recipe_create_missing_title_raises():
    with pytest.raises(ValidationError):
        RecipeCreateRequest(instructions="Do stuff", servings=2)  # type: ignore[call-arg]


def test_recipe_create_servings_zero_raises():
    with pytest.raises(ValidationError):
        RecipeCreateRequest(title="Test", instructions="Do stuff", servings=0)


def test_recipe_create_servings_over_limit_raises():
    with pytest.raises(ValidationError):
        RecipeCreateRequest(title="Test", instructions="Do stuff", servings=101)


def test_recipe_update_all_optional():
    u = RecipeUpdateRequest()
    assert u.title is None
    assert u.servings is None
    assert u.ingredients is None


def test_recipe_update_partial():
    u = RecipeUpdateRequest(servings=2, is_vegetarian=True)
    assert u.servings == 2
    assert u.is_vegetarian is True
    assert u.title is None


def test_ingredient_name_empty_raises():
    with pytest.raises(ValidationError):
        IngredientIn(name="")
