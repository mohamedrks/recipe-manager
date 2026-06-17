import uuid
from datetime import datetime

from pydantic import AliasPath, BaseModel, Field


class IngredientIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    quantity: str | None = Field(default=None, max_length=50)
    unit: str | None = Field(default=None, max_length=30)


class IngredientResponse(BaseModel):
    name: str = Field(validation_alias=AliasPath("ingredient", "name"))
    quantity: str | None = None
    unit: str | None = None

    model_config = {"from_attributes": True, "populate_by_name": True}


class RecipeCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    instructions: str = Field(min_length=1)
    servings: int = Field(ge=1, le=100)
    is_vegetarian: bool = False
    ingredients: list[IngredientIn] = Field(default_factory=list)


class RecipeUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    instructions: str | None = Field(default=None, min_length=1)
    servings: int | None = Field(default=None, ge=1, le=100)
    is_vegetarian: bool | None = None
    ingredients: list[IngredientIn] | None = None


class RecipeResponse(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    title: str
    description: str | None
    instructions: str
    servings: int
    is_vegetarian: bool
    created_at: datetime
    updated_at: datetime
    ingredients: list[IngredientResponse] = []

    model_config = {"from_attributes": True}
