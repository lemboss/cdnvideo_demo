from collections.abc import AsyncIterator

import httpx
import pytest
import pytest_asyncio

from app.core.config import Environment, Settings
from app.domain.errors import GeocodingNoResult
from app.domain.models import Coordinates, GeocodedCity
from app.main import create_app

TEST_API_KEY = "test-api-key"
TEST_YANDEX_GEOCODER_API_KEY = "test-yandex-geocoder-api-key"


class FakeGeocoder:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.coordinates: dict[str, Coordinates] = {
            "Москва": Coordinates(latitude=55.755864, longitude=37.617698),
            "Санкт-Петербург": Coordinates(latitude=59.939099, longitude=30.315877),
            "Казань": Coordinates(latitude=55.796127, longitude=49.106414),
        }

    async def geocode_city(self, name: str) -> GeocodedCity:
        self.calls.append(name)
        if name not in self.coordinates:
            raise GeocodingNoResult(details={"city": name})
        return GeocodedCity(name=name, coordinates=self.coordinates[name])


class FakeRedis:
    def __init__(self) -> None:
        self.values: dict[str, int] = {}
        self.expirations: dict[str, int] = {}

    async def incr(self, key: str) -> int:
        self.values[key] = self.values.get(key, 0) + 1
        return self.values[key]

    async def expire(self, key: str, seconds: int) -> bool:
        self.expirations[key] = seconds
        return True

    async def ping(self) -> bool:
        return True


@pytest.fixture
def api_key() -> str:
    return TEST_API_KEY


@pytest.fixture
def test_settings(tmp_path, api_key: str) -> Settings:
    return Settings(
        environment=Environment.TESTING,
        api_key=api_key,
        database_url=f"sqlite+aiosqlite:///{tmp_path / 'cities.db'}",
        auto_create_schema=True,
        rate_limit_enabled=False,
        cors_origins=["https://client.example"],
        yandex_geocoder_api_key=TEST_YANDEX_GEOCODER_API_KEY,
    )


@pytest_asyncio.fixture
async def api_client(
    test_settings: Settings,
) -> AsyncIterator[tuple[httpx.AsyncClient, FakeGeocoder]]:
    geocoder = FakeGeocoder()
    app = create_app(settings=test_settings, geocoder_client=geocoder)
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            yield client, geocoder
