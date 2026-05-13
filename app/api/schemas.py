from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.models import City, NearestCity


class CityCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        stripped = " ".join(value.strip().split())
        if not stripped:
            raise ValueError("City name must not be blank.")
        return stripped


class CityResponse(BaseModel):
    id: int
    name: str
    latitude: float
    longitude: float
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, city: City) -> "CityResponse":
        return cls(
            id=city.id,
            name=city.name,
            latitude=city.coordinates.latitude,
            longitude=city.coordinates.longitude,
            created_at=city.created_at,
            updated_at=city.updated_at,
        )


class CityListResponse(BaseModel):
    items: list[CityResponse]
    total: int
    offset: int
    limit: int


class NearestCityResponse(CityResponse):
    distance_km: float

    @classmethod
    def from_domain(cls, nearest: NearestCity) -> "NearestCityResponse":
        return cls(
            id=nearest.city.id,
            name=nearest.city.name,
            latitude=nearest.city.coordinates.latitude,
            longitude=nearest.city.coordinates.longitude,
            created_at=nearest.city.created_at,
            updated_at=nearest.city.updated_at,
            distance_km=nearest.distance_km,
        )


class DependencyHealth(BaseModel):
    status: Literal["ok", "error", "skipped"]
    detail: str | None = None


class HealthResponse(BaseModel):
    status: Literal["ok", "error"]
    version: str
    dependencies: dict[str, DependencyHealth]


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    request_id: str


class ErrorResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"error": {"code": "VALIDATION_ERROR"}}]}
    )

    error: ErrorBody
