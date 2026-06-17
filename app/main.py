from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.v1.routers.auth import router as auth_router
from app.api.v1.routers.recipes import router as recipes_router
from app.core.config import settings
from app.core.exceptions import (
    ConflictException,
    ForbiddenException,
    NotFoundException,
    UnauthorizedException,
)
from app.core.logging import setup_logging
from app.db.session import engine

setup_logging(settings.log_level)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("startup", app_name=settings.app_name, environment=settings.environment)
    yield
    await engine.dispose()
    logger.info("shutdown")


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


@app.exception_handler(ConflictException)
async def conflict_handler(request: Request, exc: ConflictException) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": exc.detail})


@app.exception_handler(UnauthorizedException)
async def unauthorized_handler(request: Request, exc: UnauthorizedException) -> JSONResponse:
    return JSONResponse(status_code=401, content={"detail": exc.detail})


@app.exception_handler(NotFoundException)
async def not_found_handler(request: Request, exc: NotFoundException) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": exc.detail})


@app.exception_handler(ForbiddenException)
async def forbidden_handler(request: Request, exc: ForbiddenException) -> JSONResponse:
    return JSONResponse(status_code=403, content={"detail": exc.detail})


app.include_router(auth_router, prefix="/api/v1")
app.include_router(recipes_router, prefix="/api/v1")


@app.get("/health/live", tags=["Health"])
async def liveness() -> dict[str, str]:
    return {"status": "ok"}
