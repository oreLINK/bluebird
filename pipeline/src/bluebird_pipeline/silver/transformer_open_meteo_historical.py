"""Silver dataset ``season_hourly``: a closed season, hour by hour, per sampling point.

One row per station, point (``station``, ``domain-N``, ``offpiste-N``), model
and hour, from the Open-Meteo Historical Forecast archive (``schedule:
season``). Several season sources can feed the dataset with different models
and variables (e.g. AROME for snowfall, ICON for snow depth); a variable a
model was not asked for is null in its rows.

Besides the silver table, the rows of each massif are written once to
``config/rewind/{rewind_id}/{massif_id}.hourly.parquet`` and committed, so the
historical KPIs can be recomputed (or new ones added) without fetching again.
The file is deterministic: sorted rows, 32-bit floats, zstd compression.
"""

from __future__ import annotations

import io
from typing import Any, ClassVar

import polars as pl

from ..bronze.base import BronzeBatch
from ..config import Massif
from ..context import RunContext
from ._open_meteo import VARIABLES, OpenMeteoParseError, _location_frame
from .base import Transformer, register_transformer

_SORT = ("station_id", "point_id", "model", "time_utc")


@register_transformer("open_meteo_historical")
class TransformerOpenMeteoHistorical(Transformer):
    """Normalise the season archive, one row per station, point and hour."""

    dataset: ClassVar[str] = "season_hourly"
    season_suffix: ClassVar[str | None] = ".hourly.parquet"
    schema: ClassVar[dict[str, Any]] = {
        "station_id": pl.Utf8,
        "point_id": pl.Utf8,
        "point_kind": pl.Utf8,  # station | domain | offpiste
        "lat": pl.Float64,
        "lon": pl.Float64,
        "elevation_m": pl.Int32,  # requested elevation, else the API terrain height
        "model": pl.Utf8,
        "time_utc": pl.Datetime("us", "UTC"),
        "snowfall_cm": pl.Float32,
        "sunshine_s": pl.Float32,
        "cloud_cover_pct": pl.Float32,
        "weather_code": pl.Int16,
        "snow_depth_m": pl.Float32,
        "relative_humidity_pct": pl.Float32,
        "cloud_cover_low_pct": pl.Float32,
        "shortwave_wm2": pl.Float32,
    }

    def transform(self, batch: BronzeBatch, ctx: RunContext) -> pl.DataFrame:
        frames: list[pl.DataFrame] = []
        for record in batch.records:
            points: list[dict[str, Any]] = record.context["points"]
            variables: list[str] = record.context["hourly"]
            models: list[str] = record.context["models"]
            unsupported = sorted(set(variables) - VARIABLES.keys())
            if unsupported:
                raise OpenMeteoParseError(f"unsupported Open-Meteo variable(s) {unsupported}")
            locations = record.payload if isinstance(record.payload, list) else [record.payload]
            if len(locations) != len(points):
                raise OpenMeteoParseError(
                    f"{record.station_id}: expected {len(points)} locations, got {len(locations)}"
                )
            for location, point in zip(locations, points, strict=True):
                elevation = point["elevation"]
                if elevation is None and location.get("elevation") is not None:
                    elevation = round(float(location["elevation"]))
                frame = _location_frame(
                    location,
                    station_id=record.station_id or "",
                    band=point["point_id"],
                    elevation=elevation,
                    variables=variables,
                    models=models,
                )
                frames.append(
                    frame.rename({"band": "point_id"}).with_columns(
                        point_kind=pl.lit(point["kind"]),
                        lat=pl.lit(point["lat"]),
                        lon=pl.lit(point["lon"]),
                    )
                )
        if not frames:
            return pl.DataFrame(schema=self.schema)
        frame = self.conform(pl.concat(frames, how="diagonal_relaxed"))
        return frame.sort(*_SORT)

    def season_columns(self) -> list[str]:
        """Columns this source fills: the canonical names of its `hourly` variables."""
        return [VARIABLES[v][0] for v in self.source.params.get("hourly", []) if v in VARIABLES]

    def season_file(self, frame: pl.DataFrame, massif: Massif, ctx: RunContext) -> bytes | None:
        stations = [ref.id for ref in ctx.stations() if ref.massif.id == massif.id]
        rows = self.conform(frame.filter(pl.col("station_id").is_in(stations))).sort(*_SORT)
        if rows.is_empty():
            return None
        buffer = io.BytesIO()
        rows.write_parquet(buffer, compression="zstd", compression_level=19, statistics=False)
        return buffer.getvalue()

    @classmethod
    def read_season(cls, content: bytes) -> pl.DataFrame:
        frame = pl.read_parquet(io.BytesIO(content))
        # Files written before a variable was added lack its column: null.
        missing = [name for name in cls.schema if name not in frame.columns]
        frame = frame.with_columns(pl.lit(None).alias(name) for name in missing)
        return frame.select(pl.col(name).cast(dtype) for name, dtype in cls.schema.items())
