from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base


class BaseRepository[ModelT: Base]:
    def __init__(self, model: type[ModelT], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    async def get_by_id(self, record_id: UUID | int) -> ModelT | None:
        return await self.session.get(self.model, record_id)

    async def delete(self, instance: ModelT) -> None:
        await self.session.delete(instance)
