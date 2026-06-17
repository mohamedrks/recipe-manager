import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.v1.deps import get_current_user, get_recipe_service
from app.models.user import User
from app.schemas.recipe import RecipeCreateRequest, RecipeResponse, RecipeUpdateRequest
from app.services.recipe_service import RecipeService

router = APIRouter(prefix="/recipes", tags=["Recipes"])


@router.post("", response_model=RecipeResponse, status_code=status.HTTP_201_CREATED)
async def create_recipe(
    payload: RecipeCreateRequest,
    service: Annotated[RecipeService, Depends(get_recipe_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> RecipeResponse:
    return await service.create(current_user, payload)


@router.get("", response_model=list[RecipeResponse])
async def list_recipes(
    service: Annotated[RecipeService, Depends(get_recipe_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[RecipeResponse]:
    return await service.list_recipes(current_user)


@router.get("/{recipe_id}", response_model=RecipeResponse)
async def get_recipe(
    recipe_id: uuid.UUID,
    service: Annotated[RecipeService, Depends(get_recipe_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> RecipeResponse:
    return await service.get(recipe_id, current_user)


@router.patch("/{recipe_id}", response_model=RecipeResponse)
async def update_recipe(
    recipe_id: uuid.UUID,
    payload: RecipeUpdateRequest,
    service: Annotated[RecipeService, Depends(get_recipe_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> RecipeResponse:
    return await service.update(recipe_id, current_user, payload)


@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recipe(
    recipe_id: uuid.UUID,
    service: Annotated[RecipeService, Depends(get_recipe_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    await service.delete(recipe_id, current_user)
