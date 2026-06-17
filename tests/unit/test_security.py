import time

import jwt
import pytest

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_hash_password_is_not_plaintext() -> None:
    hashed = hash_password("SecurePass123")
    assert hashed != "SecurePass123"


def test_verify_password_correct() -> None:
    hashed = hash_password("SecurePass123")
    assert verify_password("SecurePass123", hashed)


def test_verify_password_wrong() -> None:
    hashed = hash_password("SecurePass123")
    assert not verify_password("WrongPassword", hashed)


def test_access_token_payload() -> None:
    token = create_access_token("user-abc")
    payload = decode_token(token)
    assert payload["sub"] == "user-abc"
    assert payload["type"] == "access"


def test_refresh_token_payload() -> None:
    token = create_refresh_token("user-abc")
    payload = decode_token(token)
    assert payload["sub"] == "user-abc"
    assert payload["type"] == "refresh"


def test_decode_invalid_token_raises() -> None:
    with pytest.raises(jwt.InvalidTokenError):
        decode_token("not.a.valid.token")


def test_decode_expired_token_raises() -> None:
    expired_payload = {"sub": "user-abc", "exp": int(time.time()) - 10, "type": "access"}
    expired_token = jwt.encode(
        expired_payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_token(expired_token)
