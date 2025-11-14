import logging
import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.logger import context

logger = logging.getLogger(__name__)

EXCLUDE_PATHS = ["/ping"]


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Middleware to set up request context for logging."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        user_id = request.headers.get("X-User-ID")

        ctx = {"request_id": request_id, "user_id": user_id}
        token = context.set(ctx)

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        context.reset(token)
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log request start/completion and duration."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        if request.url.path in EXCLUDE_PATHS:
            return await call_next(request)

        start_time = time.perf_counter()
        logger.info(
            "Request started",
            extra={
                "http.method": request.method,
                "http.route": request.url.path,
            },
        )

        response = await call_next(request)
        process_time = str(time.perf_counter() - start_time)

        logger.info(
            "Request completed",
            extra={
                "http.method": request.method,
                "http.route": request.url.path,
                "http.status_code": response.status_code,
                "http.user_agent": request.headers.get("User-Agent"),
                "http.client_ip": request.client.host if request.client else None,
                "duration_ms": process_time,
            },
        )
        return response
