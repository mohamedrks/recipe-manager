import pytest
from pydantic import ValidationError

from app.schemas.auth import UserCreate


def test_valid_user_create() -> None:
    user = UserCreate(email="test@example.com", password="SecurePass123")
    assert user.email == "test@example.com"


def test_invalid_email_rejected() -> None:
    with pytest.raises(ValidationError):
        UserCreate(email="not-an-email", password="SecurePass123")


def test_password_too_short_rejected() -> None:
    with pytest.raises(ValidationError):
        UserCreate(email="test@example.com", password="short")


def test_password_too_long_rejected() -> None:
    with pytest.raises(ValidationError):
        UserCreate(email="test@example.com", password="x" * 101)
