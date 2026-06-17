import uuid

from sqlalchemy import Select, delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.ingredient import Ingredient
from app.models.recipe import Recipe, RecipeIngredient
from app.schemas.recipe import IngredientIn, RecipeCreateRequest


class RecipeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # --- query helpers ---

    def _base_query(self) -> Select[tuple[Recipe]]:
        return select(Recipe).options(
            selectinload(Recipe.ingredients).selectinload(RecipeIngredient.ingredient)
        )

    async def _fetch(self, recipe_id: uuid.UUID) -> Recipe:
        result = await self.session.execute(self._base_query().where(Recipe.id == recipe_id))
        recipe: Recipe = result.scalar_one()
        return recipe

    # --- public interface ---

    async def get_by_id(self, recipe_id: uuid.UUID, owner_id: uuid.UUID) -> Recipe | None:
        result = await self.session.execute(
            self._base_query().where(Recipe.id == recipe_id, Recipe.owner_id == owner_id)
        )
        recipe: Recipe | None = result.scalar_one_or_none()
        return recipe

    async def list_by_owner(self, owner_id: uuid.UUID) -> list[Recipe]:
        result = await self.session.execute(
            self._base_query().where(Recipe.owner_id == owner_id).order_by(Recipe.created_at.desc())
        )
        recipes: list[Recipe] = list(result.scalars().all())
        return recipes

    async def create(self, owner_id: uuid.UUID, data: RecipeCreateRequest) -> Recipe:
        recipe = Recipe(
            owner_id=owner_id,
            title=data.title,
            description=data.description,
            instructions=data.instructions,
            servings=data.servings,
            is_vegetarian=data.is_vegetarian,
        )
        self.session.add(recipe)
        await self.session.flush()
        await self._replace_ingredients(recipe.id, data.ingredients)
        await self.session.flush()
        return await self._fetch(recipe.id)

    async def update(self, recipe: Recipe, ingredients: list[IngredientIn] | None = None) -> Recipe:
        if ingredients is not None:
            await self._replace_ingredients(recipe.id, ingredients)
        await self.session.flush()
        return await self._fetch(recipe.id)

    async def delete(self, recipe_id: uuid.UUID, owner_id: uuid.UUID) -> bool:
        result = await self.session.execute(
            delete(Recipe)
            .where(Recipe.id == recipe_id, Recipe.owner_id == owner_id)
            .returning(Recipe.id)
        )
        return result.scalar_one_or_none() is not None

    # --- private helpers ---

    async def _replace_ingredients(
        self, recipe_id: uuid.UUID, ingredients: list[IngredientIn]
    ) -> None:
        await self.session.execute(
            delete(RecipeIngredient).where(RecipeIngredient.recipe_id == recipe_id)
        )
        if not ingredients:
            return
        names = [i.name.strip().lower() for i in ingredients]
        await self.session.execute(
            pg_insert(Ingredient)
            .values([{"name": n} for n in names])
            .on_conflict_do_nothing(index_elements=["name"])
        )
        rows = await self.session.execute(
            select(Ingredient.id, Ingredient.name).where(Ingredient.name.in_(names))
        )
        name_to_id = {row.name: row.id for row in rows}
        for ing, norm in zip(ingredients, names, strict=False):
            self.session.add(
                RecipeIngredient(
                    recipe_id=recipe_id,
                    ingredient_id=name_to_id[norm],
                    quantity=ing.quantity,
                    unit=ing.unit,
                )
            )
