from app.domain.distance import haversine_distance_km
from app.domain.errors import CityNotFound, DuplicateCity
from app.domain.models import (
    City,
    CityCreateResult,
    CityListResult,
    Coordinates,
    NearestCity,
    normalize_city_name,
)
from app.domain.ports import CityRepository, GeocodingClient


class CityService:
    def __init__(self, *, repository: CityRepository, geocoder: GeocodingClient) -> None:
        self._repository = repository
        self._geocoder = geocoder

    async def add_city(self, name: str) -> CityCreateResult:
        display_name = " ".join(name.strip().split())
        normalized_name = normalize_city_name(display_name)
        existing = await self._repository.get_by_normalized_name(normalized_name)
        if existing:
            return CityCreateResult(city=existing, created=False)

        geocoded = await self._geocoder.geocode_city(display_name)
        try:
            city = await self._repository.create(
                name=display_name,
                normalized_name=normalized_name,
                coordinates=geocoded.coordinates,
            )
        except DuplicateCity:
            existing_after_race = await self._repository.get_by_normalized_name(normalized_name)
            if existing_after_race:
                return CityCreateResult(city=existing_after_race, created=False)
            raise
        return CityCreateResult(city=city, created=True)

    async def get_city(self, city_id: int) -> City:
        city = await self._repository.get_by_id(city_id)
        if city is None:
            raise CityNotFound(details={"city_id": city_id})
        return city

    async def list_cities(self, *, offset: int, limit: int) -> CityListResult:
        items, total = await self._repository.list(offset=offset, limit=limit)
        return CityListResult(items=items, total=total)

    async def delete_city(self, city_id: int) -> None:
        deleted = await self._repository.delete(city_id)
        if not deleted:
            raise CityNotFound(details={"city_id": city_id})

    async def find_nearest(
        self, *, latitude: float, longitude: float, limit: int = 2
    ) -> list[NearestCity]:
        origin = Coordinates(latitude=latitude, longitude=longitude)
        cities = await self._repository.list_all()
        nearest = [
            NearestCity(
                city=city,
                distance_km=round(haversine_distance_km(origin, city.coordinates), 6),
            )
            for city in cities
        ]
        nearest.sort(key=lambda item: item.distance_km)
        return nearest[:limit]
