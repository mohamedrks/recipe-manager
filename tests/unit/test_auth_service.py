import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import ConflictException, UnauthorizedException
from app.core.security import create_refresh_token, hash_password
from app.models.user import User
from app.schemas.auth import UserCreate
from app.services.auth_service import AuthService


def make_user(email: str = "user@example.com") -> User:
    user = User()
    user.id = uuid.uuid4()
    user.email = email
    user.hashed_password = hash_password("SecurePass123")
    user.created_at = datetime.now(UTC)
    return user


def make_service(
    user: User | None = None,
    redis_exists: int = 0,
) -> AuthService:
    repo = MagicMock()
    repo.get_by_email = AsyncMock(return_value=user)
    repo.create = AsyncMock(return_value=user or make_user())

    redis = MagicMock()
    redis.exists = AsyncMock(return_value=redis_exists)
    redis.set = AsyncMock()

    return AuthService(user_repo=repo, redis=redis)


# --- register ---


async def test_register_new_user() -> None:
    service = make_service(user=None)
    result = await service.register(UserCreate(email="new@example.com", password="SecurePass123"))
    assert result.email == make_user().email


async def test_register_duplicate_email_raises() -> None:
    service = make_service(user=make_user())
    with pytest.raises(ConflictException) as exc:
        await service.register(UserCreate(email="user@example.com", password="SecurePass123"))
    assert exc.value.detail == "Email already registered"


# --- login ---


async def test_login_valid_credentials() -> None:
    service = make_service(user=make_user())
    token = await service.login("user@example.com", "SecurePass123")
    assert token.access_token
    assert token.refresh_token


async def test_login_unknown_email_raises() -> None:
    service = make_service(user=None)
    with pytest.raises(UnauthorizedException) as exc:
        await service.login("unknown@example.com", "SecurePass123")
    assert exc.value.detail == "Invalid credentials"


async def test_login_wrong_password_raises() -> None:
    service = make_service(user=make_user())
    with pytest.raises(UnauthorizedException) as exc:
        await service.login("user@example.com", "WrongPassword")
    assert exc.value.detail == "Invalid credentials"


# --- logout ---


async def test_logout_blacklists_token() -> None:
    service = make_service(user=make_user())
    token = create_refresh_token(str(uuid.uuid4()))
    await service.logout(token)
    service.redis.set.assert_called_once()


async def test_logout_invalid_token_does_not_raise() -> None:
    service = make_service()
    await service.logout("not.a.valid.token")


# --- refresh ---


async def test_refresh_valid_token_returns_new_pair() -> None:
    service = make_service(redis_exists=0)
    token = create_refresh_token(str(uuid.uuid4()))
    result = await service.refresh(token)
    assert result.access_token
    assert result.refresh_token


async def test_refresh_blacklisted_token_raises() -> None:
    service = make_service(redis_exists=1)
    token = create_refresh_token(str(uuid.uuid4()))
    with pytest.raises(UnauthorizedException) as exc:
        await service.refresh(token)
    assert exc.value.detail == "Token has been revoked"


async def test_refresh_invalid_token_raises() -> None:
    service = make_service()
    with pytest.raises(UnauthorizedException) as exc:
        await service.refresh("bad.token.here")
    assert exc.value.detail == "Invalid token"
