from math import asin, cos, radians, sin, sqrt

from app.domain.models import Coordinates

EARTH_RADIUS_KM = 6371.0088


def haversine_distance_km(origin: Coordinates, destination: Coordinates) -> float:
    lat1 = radians(origin.latitude)
    lon1 = radians(origin.longitude)
    lat2 = radians(destination.latitude)
    lon2 = radians(destination.longitude)

    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1

    a = sin(delta_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * asin(sqrt(a))
