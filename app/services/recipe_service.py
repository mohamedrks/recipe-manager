import uuid

from app.core.exceptions import NotFoundException
from app.models.user import User
from app.repositories.recipe_repository import RecipeRepository
from app.schemas.recipe import RecipeCreateRequest, RecipeResponse, RecipeUpdateRequest


class RecipeService:
    def __init__(self, repo: RecipeRepository) -> None:
        self.repo = repo

    async def create(self, owner: User, data: RecipeCreateRequest) -> RecipeResponse:
        recipe = await self.repo.create(owner.id, data)
        return RecipeResponse.model_validate(recipe)

    async def get(self, recipe_id: uuid.UUID, owner: User) -> RecipeResponse:
        recipe = await self.repo.get_by_id(recipe_id, owner.id)
        if recipe is None:
            raise NotFoundException("Recipe not found")
        return RecipeResponse.model_validate(recipe)

    async def list_recipes(self, owner: User) -> list[RecipeResponse]:
        recipes = await self.repo.list_by_owner(owner.id)
        return [RecipeResponse.model_validate(r) for r in recipes]

    async def update(
        self, recipe_id: uuid.UUID, owner: User, data: RecipeUpdateRequest
    ) -> RecipeResponse:
        recipe = await self.repo.get_by_id(recipe_id, owner.id)
        if recipe is None:
            raise NotFoundException("Recipe not found")
        update_fields = data.model_dump(exclude_unset=True, exclude={"ingredients"})
        for field, value in update_fields.items():
            setattr(recipe, field, value)
        updated = await self.repo.update(recipe, data.ingredients)
        return RecipeResponse.model_validate(updated)

    async def delete(self, recipe_id: uuid.UUID, owner: User) -> None:
        deleted = await self.repo.delete(recipe_id, owner.id)
        if not deleted:
            raise NotFoundException("Recipe not found")
