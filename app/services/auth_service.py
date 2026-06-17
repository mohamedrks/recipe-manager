import time
from typing import Any

import jwt
import redis.asyncio as aioredis

from app.core.exceptions import ConflictException, UnauthorizedException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    token_hash,
    verify_password,
)
from app.repositories.user_repository import UserRepository
from app.schemas.auth import Token, UserCreate, UserOut


class AuthService:
    def __init__(self, user_repo: UserRepository, redis: aioredis.Redis) -> None:
        self.user_repo = user_repo
        self.redis = redis

    async def register(self, payload: UserCreate) -> UserOut:
        if await self.user_repo.get_by_email(payload.email):
            raise ConflictException("Email already registered")
        user = await self.user_repo.create(
            email=payload.email,
            hashed_password=hash_password(payload.password),
        )
        return UserOut.model_validate(user)

    async def login(self, email: str, password: str) -> Token:
        user = await self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise UnauthorizedException("Invalid credentials")
        return Token(
            access_token=create_access_token(str(user.id)),
            refresh_token=create_refresh_token(str(user.id)),
        )

    async def refresh(self, refresh_token: str) -> Token:
        payload = self._decode_or_raise(refresh_token)
        if payload.get("type") != "refresh":
            raise UnauthorizedException("Invalid token type")
        if await self.redis.exists(f"blacklist:{token_hash(refresh_token)}"):
            raise UnauthorizedException("Token has been revoked")
        user_id: str = payload["sub"]
        await self._blacklist(refresh_token, payload)
        return Token(
            access_token=create_access_token(user_id),
            refresh_token=create_refresh_token(user_id),
        )

    async def logout(self, refresh_token: str) -> None:
        try:
            payload = decode_token(refresh_token)
        except jwt.InvalidTokenError:
            return
        await self._blacklist(refresh_token, payload)

    def _decode_or_raise(self, token: str) -> dict[str, Any]:
        try:
            return decode_token(token)
        except jwt.InvalidTokenError as err:
            raise UnauthorizedException("Invalid token") from err

    async def _blacklist(self, token: str, payload: dict[str, Any]) -> None:
        ttl = int(payload.get("exp", 0)) - int(time.time())
        if ttl > 0:
            await self.redis.set(f"blacklist:{token_hash(token)}", "1", ex=ttl)
