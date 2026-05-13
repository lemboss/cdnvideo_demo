from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.domain.errors import GeocodingUnavailable
from app.domain.models import City, Coordinates, GeocodedCity
from app.services.city_service import CityService


class InMemoryCityRepository:
    def __init__(self) -> None:
        self.items: dict[int, City] = {}
        self.next_id = 1

    async def get_by_id(self, city_id: int) -> City | None:
        return self.items.get(city_id)

    async def get_by_normalized_name(self, normalized_name: str) -> City | None:
        return next(
            (city for city in self.items.values() if city.normalized_name == normalized_name), None
        )

    async def list(self, *, offset: int, limit: int) -> tuple[list[City], int]:
        cities = list(self.items.values())
        return cities[offset : offset + limit], len(cities)

    async def list_all(self) -> list[City]:
        return list(self.items.values())

    async def create(self, *, name: str, normalized_name: str, coordinates: Coordinates) -> City:
        now = datetime.now(UTC)
        city = City(
            id=self.next_id,
            name=name,
            normalized_name=normalized_name,
            coordinates=coordinates,
            created_at=now,
            updated_at=now,
        )
        self.items[city.id] = city
        self.next_id += 1
        return city

    async def delete(self, city_id: int) -> bool:
        return self.items.pop(city_id, None) is not None


class FakeGeocoder:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.calls = 0

    async def geocode_city(self, name: str) -> GeocodedCity:
        self.calls += 1
        if self.fail:
            raise GeocodingUnavailable()
        return GeocodedCity(name=name, coordinates=Coordinates(latitude=55.0, longitude=37.0))


@pytest.mark.asyncio
async def test_add_city_geocodes_and_persists() -> None:
    repository = InMemoryCityRepository()
    geocoder = FakeGeocoder()
    service = CityService(repository=repository, geocoder=geocoder)

    result = await service.add_city(" Москва ")

    assert result.created is True
    assert result.city.name == "Москва"
    assert result.city.coordinates.latitude == 55.0
    assert geocoder.calls == 1


@pytest.mark.asyncio
async def test_add_city_duplicate_returns_existing_without_geocoding_again() -> None:
    repository = InMemoryCityRepository()
    geocoder = FakeGeocoder()
    service = CityService(repository=repository, geocoder=geocoder)

    first = await service.add_city("Москва")
    second = await service.add_city("  москва  ")

    assert first.created is True
    assert second.created is False
    assert second.city.id == first.city.id
    assert geocoder.calls == 1


@pytest.mark.asyncio
async def test_geocoder_failure_does_not_persist_city() -> None:
    repository = InMemoryCityRepository()
    service = CityService(repository=repository, geocoder=FakeGeocoder(fail=True))

    with pytest.raises(GeocodingUnavailable):
        await service.add_city("Москва")

    assert await repository.list_all() == []


@pytest.mark.asyncio
async def test_find_nearest_returns_two_sorted_cities() -> None:
    repository = InMemoryCityRepository()
    service = CityService(repository=repository, geocoder=FakeGeocoder())
    await repository.create(
        name="Москва",
        normalized_name="москва",
        coordinates=Coordinates(latitude=55.755864, longitude=37.617698),
    )
    await repository.create(
        name="Санкт-Петербург",
        normalized_name="санкт-петербург",
        coordinates=Coordinates(latitude=59.939099, longitude=30.315877),
    )
    await repository.create(
        name="Казань",
        normalized_name="казань",
        coordinates=Coordinates(latitude=55.796127, longitude=49.106414),
    )

    nearest = await service.find_nearest(latitude=55.75, longitude=37.61)

    assert [item.city.name for item in nearest] == ["Москва", "Санкт-Петербург"]
    assert nearest[0].distance_km < nearest[1].distance_km
