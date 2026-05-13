from app.domain.distance import haversine_distance_km
from app.domain.models import Coordinates


def test_haversine_distance_between_moscow_and_spb_is_close() -> None:
    moscow = Coordinates(latitude=55.755864, longitude=37.617698)
    spb = Coordinates(latitude=59.939099, longitude=30.315877)

    distance = haversine_distance_km(moscow, spb)

    assert 630 <= distance <= 640
