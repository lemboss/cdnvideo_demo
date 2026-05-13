from fastapi import APIRouter, Query, Response, status

from app.api.deps import CityServiceDep, RequireApiKey
from app.api.schemas import (
    CityCreateRequest,
    CityListResponse,
    CityResponse,
    NearestCityResponse,
)

router = APIRouter(prefix="/cities", tags=["cities"], dependencies=[RequireApiKey])


@router.post("", response_model=CityResponse, status_code=status.HTTP_201_CREATED)
async def create_city(
    payload: CityCreateRequest,
    response: Response,
    service: CityServiceDep,
) -> CityResponse:
    result = await service.add_city(payload.name)
    response.status_code = status.HTTP_201_CREATED if result.created else status.HTTP_200_OK
    return CityResponse.from_domain(result.city)


@router.get("", response_model=CityListResponse)
async def list_cities(
    service: CityServiceDep,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
) -> CityListResponse:
    result = await service.list_cities(offset=offset, limit=limit)
    return CityListResponse(
        items=[CityResponse.from_domain(city) for city in result.items],
        total=result.total,
        offset=offset,
        limit=limit,
    )


@router.get("/nearest", response_model=list[NearestCityResponse])
async def find_nearest_cities(
    service: CityServiceDep,
    lat: float = Query(ge=-90, le=90),
    lon: float = Query(ge=-180, le=180),
) -> list[NearestCityResponse]:
    result = await service.find_nearest(latitude=lat, longitude=lon, limit=2)
    return [NearestCityResponse.from_domain(item) for item in result]


@router.get("/{city_id}", response_model=CityResponse)
async def get_city(
    city_id: int,
    service: CityServiceDep,
) -> CityResponse:
    city = await service.get_city(city_id)
    return CityResponse.from_domain(city)


@router.delete("/{city_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_city(
    city_id: int,
    service: CityServiceDep,
) -> Response:
    await service.delete_city(city_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
