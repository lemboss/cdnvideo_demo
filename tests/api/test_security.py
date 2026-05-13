import httpx
import pytest

from app.core.config import Environment, Settings
from app.main import create_app
from tests.conftest import TEST_API_KEY, TEST_YANDEX_GEOCODER_API_KEY, FakeGeocoder, FakeRedis


@pytest.mark.asyncio
async def test_request_body_size_limit(tmp_path) -> None:
    settings = Settings(
        environment=Environment.TESTING,
        api_key=TEST_API_KEY,
        database_url=f"sqlite+aiosqlite:///{tmp_path / 'body.db'}",
        auto_create_schema=True,
        rate_limit_enabled=False,
        max_request_body_bytes=10,
        yandex_geocoder_api_key=TEST_YANDEX_GEOCODER_API_KEY,
    )
    app = create_app(settings=settings, geocoder_client=FakeGeocoder())
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/cities",
                json={"name": "Москва"},
                headers={"X-API-Key": TEST_API_KEY},
            )

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "REQUEST_BODY_TOO_LARGE"


@pytest.mark.asyncio
async def test_rate_limit_uses_redis(tmp_path) -> None:
    settings = Settings(
        environment=Environment.TESTING,
        api_key=TEST_API_KEY,
        database_url=f"sqlite+aiosqlite:///{tmp_path / 'rate.db'}",
        auto_create_schema=True,
        rate_limit_enabled=True,
        rate_limit_requests_per_minute=1,
        yandex_geocoder_api_key=TEST_YANDEX_GEOCODER_API_KEY,
    )
    app = create_app(settings=settings, geocoder_client=FakeGeocoder(), redis_client=FakeRedis())
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            headers = {"X-API-Key": TEST_API_KEY}
            first = await client.get("/cities", headers=headers)
            second = await client.get("/cities", headers=headers)

    assert first.status_code == 200
    assert second.status_code == 429
    assert second.json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"
