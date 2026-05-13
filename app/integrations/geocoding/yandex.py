import httpx
from pydantic import SecretStr

from app.domain.errors import GeocodingNoResult, GeocodingUnavailable
from app.domain.models import Coordinates, GeocodedCity


class YandexGeocodingClient:
    def __init__(
        self,
        *,
        api_key: SecretStr | None,
        base_url: str,
        timeout_seconds: float,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url
        self._client = httpx.AsyncClient(timeout=timeout_seconds)

    async def geocode_city(self, name: str) -> GeocodedCity:
        if self._api_key is None or not self._api_key.get_secret_value():
            raise GeocodingUnavailable("Yandex geocoder API key is not configured.")

        try:
            response = await self._client.get(
                self._base_url,
                params={
                    "apikey": self._api_key.get_secret_value(),
                    "geocode": name,
                    "lang": "ru_RU",
                    "format": "json",
                },
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise GeocodingUnavailable("Yandex geocoder request failed.") from exc

        try:
            return self._parse_response(response.json(), fallback_name=name)
        except GeocodingNoResult:
            raise
        except Exception as exc:
            raise GeocodingUnavailable("Yandex geocoder response is invalid.") from exc

    async def close(self) -> None:
        await self._client.aclose()

    @staticmethod
    def _parse_response(payload: dict[str, object], *, fallback_name: str) -> GeocodedCity:
        collection = payload["response"]["GeoObjectCollection"]  # type: ignore[index]
        feature_members = collection.get("featureMember", [])  # type: ignore[union-attr]
        if not feature_members:
            raise GeocodingNoResult(details={"city": fallback_name})

        geo_object = feature_members[0]["GeoObject"]  # type: ignore[index]
        point_pos = geo_object["Point"]["pos"]  # type: ignore[index]
        lon_raw, lat_raw = str(point_pos).split()
        longitude = float(lon_raw)
        latitude = float(lat_raw)
        return GeocodedCity(
            name=str(geo_object.get("name") or fallback_name),
            coordinates=Coordinates(latitude=latitude, longitude=longitude),
        )
