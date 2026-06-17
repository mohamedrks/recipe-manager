import uuid
from collections.abc import AsyncGenerator
from typing import Annotated

import jwt
import redis.asyncio as aioredis
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedException
from app.core.security import decode_token
from app.db.redis import redis_client
from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.repositories.recipe_repository import RecipeRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.recipe_service import RecipeService

bearer_scheme = HTTPBearer()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_redis() -> aioredis.Redis:
    return redis_client


async def get_auth_service(
    session: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
) -> AuthService:
    return AuthService(UserRepository(session), redis)


async def get_recipe_service(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> RecipeService:
    return RecipeService(RecipeRepository(session))


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    token = credentials.credentials
    try:
        payload = decode_token(token)
    except jwt.InvalidTokenError as err:
        raise UnauthorizedException("Invalid token") from err
    if payload.get("type") != "access":
        raise UnauthorizedException("Invalid token type")
    user_id: str = payload["sub"]
    repo = UserRepository(session)
    user = await repo.get_by_id(uuid.UUID(user_id))
    if not user:
        raise UnauthorizedException("User not found")
    return user
