"""Small geodesic helpers on ``[lon, lat]`` points (degrees), shared by layers."""

from __future__ import annotations

import math
from itertools import pairwise

EARTH_RADIUS_M = 6_371_000.0
_M_PER_DEG_LAT = math.pi * EARTH_RADIUS_M / 180


def distance_m(a: list[float], b: list[float]) -> float:
    """Great-circle distance between two ``[lon, lat]`` points (haversine)."""
    (lon1, lat1), (lon2, lat2) = a[:2], b[:2]
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = phi2 - phi1
    dlambda = math.radians(lon2 - lon1)
    h = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(h))


def path_length_m(points: list[list[float]]) -> float:
    """Length of a polyline of ``[lon, lat]`` points."""
    return sum(distance_m(a, b) for a, b in pairwise(points))


def offset(point: list[float], distance: float, bearing_deg: float) -> list[float]:
    """``[lon, lat]`` at ``distance`` metres from ``point`` towards ``bearing_deg``.

    Flat-earth approximation, accurate to a few metres over a few kilometres.
    """
    lon, lat = point[:2]
    theta = math.radians(bearing_deg)
    dlat = distance * math.cos(theta) / _M_PER_DEG_LAT
    dlon = distance * math.sin(theta) / (_M_PER_DEG_LAT * math.cos(math.radians(lat)))
    return [lon + dlon, lat + dlat]
