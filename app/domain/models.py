from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Coordinates:
    latitude: float
    longitude: float

    def __post_init__(self) -> None:
        if not -90 <= self.latitude <= 90:
            raise ValueError("Latitude must be between -90 and 90.")
        if not -180 <= self.longitude <= 180:
            raise ValueError("Longitude must be between -180 and 180.")


@dataclass(frozen=True, slots=True)
class City:
    id: int
    name: str
    normalized_name: str
    coordinates: Coordinates
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class GeocodedCity:
    name: str
    coordinates: Coordinates


@dataclass(frozen=True, slots=True)
class NearestCity:
    city: City
    distance_km: float


@dataclass(frozen=True, slots=True)
class CityCreateResult:
    city: City
    created: bool


@dataclass(frozen=True, slots=True)
class CityListResult:
    items: list[City]
    total: int


def normalize_city_name(name: str) -> str:
    return " ".join(name.strip().casefold().split())
