"""Where to sample a station's weather for a season review (Rewind).

Three kinds of points per station, all deterministic:

- ``station``: the station coordinates at the elevation of one band (like the
  live KPIs);
- ``domain``: points spread at equal distances along the station's pistes
  (OSM reference data ``domain_features``), so the season total reflects the
  whole ski area;
- ``offpiste``: points on a ring around the domain: from the centre of the
  pistes, at the distance of the farthest piste plus a margin, at equal
  bearings.

Domain and off-piste points carry no elevation: Open-Meteo then uses its own
terrain model for the point. A station without pistes has no domain or
off-piste point.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from itertools import pairwise
from typing import Any, Literal

import polars as pl

from ..config import Band, StationRef
from ..geo import distance_m, offset, path_length_m

PointKind = Literal["station", "domain", "offpiste"]
_DECIMALS = 4  # ~10 m: enough for a 1.5 km grid, stable in diffs


@dataclass(frozen=True)
class SamplePoint:
    point_id: str
    kind: PointKind
    lat: float
    lon: float
    elevation: int | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _point(point_id: str, kind: PointKind, lonlat: list[float]) -> SamplePoint:
    return SamplePoint(
        point_id=point_id,
        kind=kind,
        lat=round(lonlat[1], _DECIMALS),
        lon=round(lonlat[0], _DECIMALS),
    )


def _along(lines: list[list[list[float]]], count: int) -> list[list[float]]:
    """``count`` points at equal distances along the concatenated ``lines``."""
    segments: list[tuple[list[float], list[float], float]] = []
    for line in lines:
        for a, b in pairwise(line):
            length = distance_m(a, b)
            if length > 0:
                segments.append((a, b, length))
    total = sum(length for _, _, length in segments)
    if total <= 0 or count <= 0:
        return []
    targets = [(i + 0.5) * total / count for i in range(count)]
    points: list[list[float]] = []
    walked = 0.0
    index = 0
    for a, b, length in segments:
        while index < count and targets[index] <= walked + length:
            t = (targets[index] - walked) / length
            points.append([a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])])
            index += 1
        walked += length
    return points


def station_points(
    ref: StationRef,
    features: pl.DataFrame | None,
    *,
    band: Band = "mid",
    domain_points: int = 8,
    offpiste_points: int = 8,
    offpiste_margin_m: float = 800.0,
) -> list[SamplePoint]:
    """The sampling points of one station, station point first."""
    station = ref.station
    points = [
        SamplePoint(
            point_id="station",
            kind="station",
            lat=station.lat,
            lon=station.lon,
            elevation=station.elevation.at(band),
        )
    ]
    if features is None:
        return points
    pistes = features.filter(
        (pl.col("station_id") == station.id) & (pl.col("feature") == "piste")
    ).sort("osm_id")
    lines = [line for line in pistes["coordinates"].to_list() if line and len(line) >= 2]
    if not lines or path_length_m([p for line in lines for p in line]) <= 0:
        return points

    for i, lonlat in enumerate(_along(lines, domain_points), start=1):
        points.append(_point(f"domain-{i}", "domain", lonlat))

    vertices = [p for line in lines for p in line]
    centre = [
        sum(p[0] for p in vertices) / len(vertices),
        sum(p[1] for p in vertices) / len(vertices),
    ]
    radius = max(distance_m(centre, p) for p in vertices) + offpiste_margin_m
    for i in range(offpiste_points):
        bearing = i * 360 / offpiste_points
        points.append(_point(f"offpiste-{i + 1}", "offpiste", offset(centre, radius, bearing)))
    return points
