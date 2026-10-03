"""Silver dataset ``domain_features``: pistes and lifts around each station.

This is reference data (``schedule: reference``): besides the silver table, it
is written to ``config/reference/domain_features/{massif}.geojson``, one
GeoJSON FeatureCollection per massif, committed to git. GitHub renders these
files as maps, which makes refresh pull requests easy to review.

The top-level ``bluebird`` member (allowed by RFC 7946 as a foreign member)
holds provenance and a per-station summary, so a station losing its pistes
after a refresh is visible at a glance in the diff.

Known limitation: features are selected within ``radius_m`` of each station,
so neighbouring resorts closer than twice the radius share some features.
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from itertools import pairwise
from typing import Any, ClassVar

import polars as pl

from ..bronze.base import BronzeBatch
from ..config import Massif
from ..context import RunContext
from .base import Transformer, register_transformer

_EARTH_RADIUS_M = 6_371_000.0
_NON_LINE_AERIALWAYS = {"station", "pylon", "goods"}
_COORD_DECIMALS = 5  # ~1 m
_DIFFICULTIES = ("novice", "easy", "intermediate", "advanced", "expert", "freeride")


def path_length_m(points: list[list[float]]) -> float:
    """Length of a polyline of ``[lon, lat]`` points (haversine)."""
    total = 0.0
    for (lon1, lat1), (lon2, lat2) in pairwise(points):
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = phi2 - phi1
        dlambda = math.radians(lon2 - lon1)
        h = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        total += 2 * _EARTH_RADIUS_M * math.asin(math.sqrt(h))
    return total


def _station_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    pistes = [r for r in rows if r["feature"] == "piste"]
    lifts = [r for r in rows if r["feature"] == "lift"]
    by_difficulty: dict[str, float] = defaultdict(float)
    for piste in pistes:
        kind = piste["kind"] if piste["kind"] in _DIFFICULTIES else "unknown"
        by_difficulty[kind] += piste["length_m"] / 1000
    return {
        "pistes": len(pistes),
        "piste_km": round(sum(p["length_m"] for p in pistes) / 1000, 1),
        "piste_km_by_difficulty": {k: round(v, 1) for k, v in sorted(by_difficulty.items())},
        "lifts": len(lifts),
        "lift_km": round(sum(lift["length_m"] for lift in lifts) / 1000, 1),
    }


@register_transformer("osm_overpass")
class TransformerOsmOverpass(Transformer):
    """One row per OSM way: a downhill piste or an aerialway, with its geometry."""

    dataset: ClassVar[str] = "domain_features"
    reference_suffix: ClassVar[str | None] = ".geojson"
    schema: ClassVar[dict[str, Any]] = {
        "station_id": pl.Utf8,
        "osm_id": pl.Int64,
        "feature": pl.Utf8,  # "piste" | "lift"
        "kind": pl.Utf8,  # piste difficulty or aerialway type
        "name": pl.Utf8,
        "length_m": pl.Float64,
        "coordinates": pl.List(pl.List(pl.Float64)),  # [[lon, lat], ...]
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
                coordinates = [
                    [round(p["lon"], _COORD_DECIMALS), round(p["lat"], _COORD_DECIMALS)]
                    for p in element.get("geometry", [])
                ]
                if len(coordinates) < 2:
                    continue
                rows.append(
                    {
                        "station_id": record.station_id,
                        "osm_id": element.get("id"),
                        "feature": feature,
                        "kind": kind,
                        "name": tags.get("name") or tags.get("piste:name"),
                        "length_m": round(path_length_m(coordinates), 1),
                        "coordinates": coordinates,
                    }
                )
        frame = pl.DataFrame(rows, schema=self.schema) if rows else pl.DataFrame(schema=self.schema)
        return (
            self.conform(frame)
            .unique(["station_id", "osm_id"], keep="first", maintain_order=True)
            .sort("station_id", "feature", "osm_id")
        )

    # -- reference file -----------------------------------------------------------

    def reference_file(self, frame: pl.DataFrame, massif: Massif, ctx: RunContext) -> bytes | None:
        station_ids = [ref.id for ref in ctx.stations() if ref.massif.id == massif.id]
        rows = (
            frame.filter(pl.col("station_id").is_in(station_ids))
            .sort("station_id", "feature", "osm_id")
            .to_dicts()
        )
        if not rows:
            return None
        by_station: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            by_station[row["station_id"]].append(row)
        meta = {
            "dataset": self.dataset,
            "massif_id": massif.id,
            "source_id": self.source.id,
            "generated_at": ctx.generated_at.isoformat().replace("+00:00", "Z"),
            "radius_m": self.source.params.get("radius_m"),
            "attribution": f"{self.source.attribution.name} ({self.source.attribution.license})",
            "summary": {sid: _station_summary(by_station[sid]) for sid in sorted(by_station)},
        }
        features = [
            json.dumps(
                {
                    "type": "Feature",
                    "id": f"way/{row['osm_id']}",
                    "properties": {
                        "station_id": row["station_id"],
                        "osm_id": row["osm_id"],
                        "feature": row["feature"],
                        "kind": row["kind"],
                        "name": row["name"],
                        "length_m": round(row["length_m"]),
                    },
                    "geometry": {"type": "LineString", "coordinates": row["coordinates"]},
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )
            for row in rows
        ]
        # One feature per line: stable, reviewable diffs.
        text = (
            '{"type":"FeatureCollection",\n"bluebird":'
            + json.dumps(meta, ensure_ascii=False, indent=1, sort_keys=True)
            + ',\n"features":[\n'
            + ",\n".join(features)
            + "\n]}\n"
        )
        return text.encode("utf-8")

    @classmethod
    def read_reference(cls, content: bytes) -> pl.DataFrame:
        collection = json.loads(content)
        rows = [
            {
                **{k: feature["properties"].get(k) for k in cls.schema if k != "coordinates"},
                "coordinates": feature["geometry"]["coordinates"],
            }
            for feature in collection.get("features", [])
        ]
        if not rows:
            return pl.DataFrame(schema=cls.schema)
        return pl.DataFrame(rows, schema=cls.schema)
