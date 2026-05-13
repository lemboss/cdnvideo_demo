from secrets import compare_digest

from fastapi import Header, Request

from app.domain.errors import ServiceUnavailable, Unauthorized


async def require_api_key(
    request: Request,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> None:
    configured_api_key = request.app.state.settings.api_key
    if configured_api_key is None or not configured_api_key.get_secret_value():
        raise ServiceUnavailable("API key is not configured.")
    expected_api_key = configured_api_key.get_secret_value()
    if not x_api_key or not compare_digest(x_api_key, expected_api_key):
        raise Unauthorized()
