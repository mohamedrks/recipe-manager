from collections.abc import AsyncGenerator

import pytest
import redis.asyncio as aioredis
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.api.v1.deps import get_db, get_redis
from app.core.config import settings
from app.main import app

# NullPool: never pools connections — each session gets a fresh asyncpg connection
# created on the current event loop, so no "attached to a different loop" errors
# even though pytest-asyncio gives each test its own event loop.
_test_engine = create_async_engine(settings.database_url, poolclass=NullPool)
_TestSession = async_sessionmaker(_test_engine, expire_on_commit=False)


async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with _TestSession() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def _override_get_redis() -> aioredis.Redis:  # type: ignore[type-arg]
    # Fresh client per request: connections are created lazily on the current
    # event loop, avoiding cross-loop issues with the module-level singleton.
    return aioredis.from_url(settings.redis_url, decode_responses=True)


app.dependency_overrides[get_db] = _override_get_db
app.dependency_overrides[get_redis] = _override_get_redis


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture(autouse=True)
async def clean_db() -> AsyncGenerator[None, None]:
    yield
    async with _test_engine.begin() as conn:
        await conn.execute(
            text(
                "TRUNCATE TABLE recipe_ingredients, recipes, users, ingredients"
                " RESTART IDENTITY CASCADE"
            )
        )
