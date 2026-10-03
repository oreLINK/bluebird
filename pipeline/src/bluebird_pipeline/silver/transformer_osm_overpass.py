"""Silver dataset ``domain_features``: pistes and lifts around each station."""

from __future__ import annotations

import math
from itertools import pairwise
from typing import Any, ClassVar

import polars as pl

from ..bronze.base import BronzeBatch
from ..context import RunContext
from .base import Transformer, register_transformer

_EARTH_RADIUS_M = 6_371_000.0
_NON_LINE_AERIALWAYS = {"station", "pylon", "goods"}


def path_length_m(points: list[dict[str, float]]) -> float:
    """Length of a polyline of ``{"lat", "lon"}`` points (haversine)."""
    total = 0.0
    for a, b in pairwise(points):
        lat1, lat2 = math.radians(a["lat"]), math.radians(b["lat"])
        dlat = lat2 - lat1
        dlon = math.radians(b["lon"] - a["lon"])
        h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        total += 2 * _EARTH_RADIUS_M * math.asin(math.sqrt(h))
    return total


@register_transformer("osm_overpass")
class TransformerOsmOverpass(Transformer):
    """One row per OSM way: a downhill piste or an aerialway."""

    dataset: ClassVar[str] = "domain_features"
    schema: ClassVar[dict[str, Any]] = {
        "station_id": pl.Utf8,
        "osm_id": pl.Int64,
        "feature": pl.Utf8,  # "piste" | "lift"
        "kind": pl.Utf8,  # piste difficulty or aerialway type
        "name": pl.Utf8,
        "length_m": pl.Float64,
    }

    def transform(self, batch: BronzeBatch, ctx: RunContext) -> pl.DataFrame:
        rows: list[dict[str, Any]] = []
        for record in batch.records:
            for element in (record.payload or {}).get("elements", []):
                if element.get("type") != "way":
                    continue
                tags: dict[str, str] = element.get("tags", {})
                aerialway = tags.get("aerialway")
                if aerialway and aerialway not in _NON_LINE_AERIALWAYS:
                    feature, kind = "lift", aerialway
                elif tags.get("piste:type") == "downhill":
                    feature, kind = "piste", tags.get("piste:difficulty")
                else:
                    continue
                rows.append(
                    {
                        "station_id": record.station_id,
                        "osm_id": element.get("id"),
                        "feature": feature,
                        "kind": kind,
                        "name": tags.get("name") or tags.get("piste:name"),
                        "length_m": path_length_m(element.get("geometry", [])),
                    }
                )
        frame = pl.DataFrame(rows, schema=self.schema) if rows else pl.DataFrame(schema=self.schema)
        return self.conform(frame).unique(["station_id", "osm_id"]).sort("station_id", "osm_id")
