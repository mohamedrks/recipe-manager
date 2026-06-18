from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.v1.routers.auth import router as auth_router
from app.api.v1.routers.health import router as health_router
from app.api.v1.routers.recipes import router as recipes_router
from app.core.config import settings
from app.core.exceptions import (
    ConflictException,
    ForbiddenException,
    NotFoundException,
    UnauthorizedException,
)
from app.core.logging import setup_logging
from app.core.middleware import RequestLoggingMiddleware
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

app.add_middleware(RequestLoggingMiddleware)


@app.exception_handler(ConflictException)
async def conflict_handler(request: Request, exc: ConflictException) -> JSONResponse:
    logger.warning("domain_exception", detail=exc.detail)
    return JSONResponse(status_code=409, content={"detail": exc.detail})


@app.exception_handler(UnauthorizedException)
async def unauthorized_handler(request: Request, exc: UnauthorizedException) -> JSONResponse:
    logger.warning("domain_exception", detail=exc.detail)
    return JSONResponse(status_code=401, content={"detail": exc.detail})


@app.exception_handler(NotFoundException)
async def not_found_handler(request: Request, exc: NotFoundException) -> JSONResponse:
    logger.warning("domain_exception", detail=exc.detail)
    return JSONResponse(status_code=404, content={"detail": exc.detail})


@app.exception_handler(ForbiddenException)
async def forbidden_handler(request: Request, exc: ForbiddenException) -> JSONResponse:
    logger.warning("domain_exception", detail=exc.detail)
    return JSONResponse(status_code=403, content={"detail": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    # Strip 'input' before logging — it may contain passwords or PII
    safe_errors = [{k: v for k, v in error.items() if k != "input"} for error in exc.errors()]
    logger.warning("validation_error", errors=safe_errors)
    return JSONResponse(status_code=422, content={"detail": safe_errors})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled_exception")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.include_router(health_router)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(recipes_router, prefix="/api/v1")
