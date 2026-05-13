import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.schemas import ErrorBody, ErrorResponse
from app.core.context import get_request_id
from app.domain.errors import AppError, InternalServiceError

logger = logging.getLogger(__name__)


def build_error_response(error: AppError, request: Request | None = None) -> dict[str, object]:
    request_id = get_request_id()
    if request is not None:
        request_id = getattr(request.state, "request_id", request_id)
    return ErrorResponse(
        error=ErrorBody(
            code=error.code,
            message=error.message,
            details=error.details,
            request_id=request_id,
        )
    ).model_dump(mode="json")


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        log_method = logger.error if exc.status_code >= 500 else logger.warning
        log_method(
            "application_error",
            extra={
                "error_code": exc.code,
                "status_code": exc.status_code,
                "path": request.url.path,
            },
            exc_info=exc if exc.status_code >= 500 else None,
        )
        headers = {}
        if exc.retry_after_seconds is not None:
            headers["Retry-After"] = str(exc.retry_after_seconds)
        return JSONResponse(
            status_code=exc.status_code,
            content=build_error_response(exc, request),
            headers=headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        error = AppError(
            code="VALIDATION_ERROR",
            message="Request validation failed.",
            status_code=422,
            details={"errors": exc.errors()},
        )
        logger.warning(
            "request_validation_error",
            extra={
                "error_code": error.code,
                "status_code": error.status_code,
                "path": request.url.path,
            },
        )
        return JSONResponse(status_code=422, content=build_error_response(error, request))

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        error = AppError(
            code="HTTP_ERROR",
            message=str(exc.detail),
            status_code=exc.status_code,
        )
        return JSONResponse(
            status_code=exc.status_code, content=build_error_response(error, request)
        )

    @app.exception_handler(Exception)
    async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
        error = InternalServiceError()
        logger.error(
            "unexpected_error",
            extra={
                "error_code": error.code,
                "status_code": error.status_code,
                "path": request.url.path,
            },
            exc_info=exc,
        )
        return JSONResponse(status_code=500, content=build_error_response(error, request))
