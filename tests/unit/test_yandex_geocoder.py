import pytest

from app.domain.errors import GeocodingNoResult
from app.integrations.geocoding.yandex import YandexGeocodingClient

YANDEX_RESPONSE = {
    "response": {
        "GeoObjectCollection": {
            "featureMember": [
                {
                    "GeoObject": {
                        "name": "Москва",
                        "Point": {
                            "pos": "37.617698 55.755864",
                        },
                    },
                }
            ],
        },
    },
}


def test_parse_yandex_response_uses_lon_lat_order() -> None:
    result = YandexGeocodingClient._parse_response(YANDEX_RESPONSE, fallback_name="Москва")

    assert result.name == "Москва"
    assert result.coordinates.longitude == 37.617698
    assert result.coordinates.latitude == 55.755864


def test_parse_empty_yandex_response_raises_no_result() -> None:
    payload = {"response": {"GeoObjectCollection": {"featureMember": []}}}

    with pytest.raises(GeocodingNoResult):
        YandexGeocodingClient._parse_response(payload, fallback_name="Город")
