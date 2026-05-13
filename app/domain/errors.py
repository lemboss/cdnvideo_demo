from typing import Any


class AppError(Exception):
    code = "APP_ERROR"
    message = "Application error."
    status_code = 500
    retry_after_seconds: int | None = None

    def __init__(
        self,
        message: str | None = None,
        *,
        code: str | None = None,
        status_code: int | None = None,
        details: dict[str, Any] | None = None,
        retry_after_seconds: int | None = None,
    ) -> None:
        self.message = message or self.message
        self.code = code or self.code
        self.status_code = status_code or self.status_code
        self.details = details or {}
        self.retry_after_seconds = retry_after_seconds
        super().__init__(self.message)


class Unauthorized(AppError):
    code = "UNAUTHORIZED"
    message = "Valid API key is required."
    status_code = 401


class CityNotFound(AppError):
    code = "CITY_NOT_FOUND"
    message = "City was not found."
    status_code = 404


class DuplicateCity(AppError):
    code = "DUPLICATE_CITY"
    message = "City already exists."
    status_code = 409


class GeocodingNoResult(AppError):
    code = "GEOCODING_NO_RESULT"
    message = "Geocoder did not return coordinates for this city."
    status_code = 422


class GeocodingUnavailable(AppError):
    code = "GEOCODING_UNAVAILABLE"
    message = "Geocoder is unavailable."
    status_code = 503


class ServiceUnavailable(AppError):
    code = "SERVICE_UNAVAILABLE"
    message = "Service dependency is unavailable."
    status_code = 503


class RepositoryError(AppError):
    code = "REPOSITORY_ERROR"
    message = "Storage operation failed."
    status_code = 500


class RequestBodyTooLarge(AppError):
    code = "REQUEST_BODY_TOO_LARGE"
    status_code = 413

    def __init__(self, *, max_body_size: int) -> None:
        super().__init__(
            message="Request body is too large.",
            details={"max_body_size": max_body_size},
        )


class RateLimitExceeded(AppError):
    code = "RATE_LIMIT_EXCEEDED"
    message = "Rate limit exceeded."
    status_code = 429


class InternalServiceError(AppError):
    code = "INTERNAL_SERVICE_ERROR"
    message = "Internal service error."
    status_code = 500
