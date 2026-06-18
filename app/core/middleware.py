import time
import uuid

import structlog
from prometheus_client import Counter, Histogram
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger()

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status_code"],
)
http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=str(uuid.uuid4()))

        start = time.perf_counter()
        response = await call_next(request)
        duration_s = time.perf_counter() - start

        path = request.url.path
        http_requests_total.labels(
            method=request.method,
            path=path,
            status_code=str(response.status_code),
        ).inc()
        http_request_duration_seconds.labels(method=request.method, path=path).observe(duration_s)

        log_kwargs = dict(
            method=request.method,
            path=path,
            status_code=response.status_code,
            duration_ms=round(duration_s * 1000, 2),
        )
        if response.status_code >= 500:
            logger.error("request", **log_kwargs)
        elif response.status_code >= 400:
            logger.warning("request", **log_kwargs)
        else:
            logger.info("request", **log_kwargs)

        return response
