import hashlib
import logging
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.context import get_request_id, request_id_var
from app.domain.errors import AppError, RateLimitExceeded, RequestBodyTooLarge, ServiceUnavailable

logger = logging.getLogger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        token = request_id_var.set(request_id)
        started_at = time.perf_counter()
        response_status = 500
        try:
            response = await call_next(request)
            response_status = response.status_code
        finally:
            duration_ms = round((time.perf_counter() - started_at) * 1000, 3)
            logger.info(
                "request_completed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response_status,
                    "duration_ms": duration_ms,
                },
            )
            request_id_var.reset(token)

        response.headers["X-Request-ID"] = request_id
        return response


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        max_body_size = request.app.state.settings.max_request_body_bytes
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                if int(content_length) > max_body_size:
                    return _app_error_response(
                        request, RequestBodyTooLarge(max_body_size=max_body_size)
                    )
            except ValueError:
                pass

        received_bytes = 0
        receive = request._receive  # noqa: SLF001

        async def limited_receive() -> dict[str, object]:
            nonlocal received_bytes
            message = await receive()
            if message["type"] == "http.request":
                received_bytes += len(message.get("body", b""))
                if received_bytes > max_body_size:
                    raise RequestBodyTooLarge(max_body_size=max_body_size)
            return message

        request._receive = limited_receive  # noqa: SLF001
        try:
            return await call_next(request)
        except RequestBodyTooLarge as exc:
            return _app_error_response(request, exc)


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        settings = request.app.state.settings
        if (
            not settings.rate_limit_enabled
            or request.method == "OPTIONS"
            or request.url.path in settings.rate_limit_exempt_paths
        ):
            return await call_next(request)

        redis = request.app.state.redis
        if redis is None:
            return _app_error_response(
                request, ServiceUnavailable("Rate limiter is not configured.")
            )

        bucket = int(time.time() // 60)
        identity = request.headers.get("X-API-Key") or (
            request.client.host if request.client else "unknown"
        )
        identity_hash = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]
        key = f"rate-limit:{identity_hash}:{bucket}"

        try:
            count = await redis.incr(key)
            if count == 1:
                await redis.expire(key, 60)
        except Exception as exc:
            logger.error("rate_limiter_unavailable", exc_info=exc)
            return _app_error_response(request, ServiceUnavailable("Rate limiter is unavailable."))

        if count > settings.rate_limit_requests_per_minute:
            retry_after = 60 - int(time.time() % 60)
            return _app_error_response(
                request,
                RateLimitExceeded(retry_after_seconds=retry_after),
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(settings.rate_limit_requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(
            max(settings.rate_limit_requests_per_minute - int(count), 0)
        )
        return response


def _app_error_response(request: Request, error: AppError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", get_request_id())
    headers = {}
    if error.retry_after_seconds is not None:
        headers["Retry-After"] = str(error.retry_after_seconds)
    return JSONResponse(
        status_code=error.status_code,
        content={
            "error": {
                "code": error.code,
                "message": error.message,
                "details": error.details,
                "request_id": request_id,
            }
        },
        headers=headers,
    )
