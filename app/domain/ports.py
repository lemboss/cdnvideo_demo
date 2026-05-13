from __future__ import annotations

from typing import Protocol

from app.domain.models import City, Coordinates, GeocodedCity


class CityRepository(Protocol):
    async def get_by_id(self, city_id: int) -> City | None:
        raise NotImplementedError

    async def get_by_normalized_name(self, normalized_name: str) -> City | None:
        raise NotImplementedError

    async def list(self, *, offset: int, limit: int) -> tuple[list[City], int]:
        raise NotImplementedError

    async def list_all(self) -> list[City]:
        raise NotImplementedError

    async def create(self, *, name: str, normalized_name: str, coordinates: Coordinates) -> City:
        raise NotImplementedError

    async def delete(self, city_id: int) -> bool:
        raise NotImplementedError


class GeocodingClient(Protocol):
    async def geocode_city(self, name: str) -> GeocodedCity:
        raise NotImplementedError
