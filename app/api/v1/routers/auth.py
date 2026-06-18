from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from app.api.v1.deps import get_auth_service, get_current_user
from app.core.limiter import limiter
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    TokenRefreshRequest,
    TokenResponse,
    UserRegisterRequest,
    UserResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def register(
    request: Request,
    payload: UserRegisterRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserResponse:
    return await service.register(payload)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(
    request: Request,
    payload: LoginRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    return await service.login(payload.email, payload.password)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    payload: TokenRefreshRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    return await service.refresh(payload.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    payload: TokenRefreshRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
    _current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    await service.logout(payload.refresh_token)
