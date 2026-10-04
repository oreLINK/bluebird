"""Parse Open-Meteo hourly responses (forecast and ensemble) into tidy rows.

Open-Meteo names hourly series ``{variable}[_memberNN][_{model_suffix}]``:

- ``snowfall``                                   single model, control run
- ``snowfall_member07``                          single model, member 7
- ``snowfall_member07_ecmwf_ifs025_ensemble``    several models, member 7
- ``snowfall_icon_seamless_eps``                 several models, control run

The model suffix may differ from the requested model id
(``ecmwf_ifs025`` -> ``ecmwf_ifs025_ensemble``), so we map it back by prefix.
The control run is stored as member 0.
"""

from __future__ import annotations

import re
from typing import Any

import polars as pl

from ..bronze.base import BronzeBatch

# Open-Meteo variable -> (canonical silver column, expected unit)
VARIABLES: dict[str, tuple[str, str]] = {
    "snowfall": ("snowfall_cm", "cm"),
    "precipitation": ("precipitation_mm", "mm"),
    "rain": ("rain_mm", "mm"),
    "temperature_2m": ("temperature_c", "°C"),
    "wind_speed_10m": ("wind_speed_kmh", "km/h"),
    "wind_gusts_10m": ("wind_gusts_kmh", "km/h"),
    "freezing_level_height": ("freezing_level_m", "m"),
    "cloud_cover": ("cloud_cover_pct", "%"),
    "sunshine_duration": ("sunshine_s", "s"),
    "weather_code": ("weather_code", "wmo code"),
    "snow_depth": ("snow_depth_m", "m"),
    "relative_humidity_2m": ("relative_humidity_pct", "%"),
    "cloud_cover_low": ("cloud_cover_low_pct", "%"),
    "shortwave_radiation": ("shortwave_wm2", "W/m²"),
}

# Units Open-Meteo reports for series it has no data for.
_NO_DATA_UNITS = {"undefined", ""}

SCHEMA: dict[str, Any] = {
    "station_id": pl.Utf8,
    "band": pl.Utf8,
    "elevation_m": pl.Int32,
    "time_utc": pl.Datetime("us", "UTC"),
    "model": pl.Utf8,
    "member": pl.Int16,
    **{column: pl.Float64 for column, _ in VARIABLES.values()},
}

_SUFFIX = re.compile(r"^(?:_member(?P<member>\d+))?(?:_(?P<model>.+))?$")


class OpenMeteoParseError(ValueError):
    """Raised when a response does not match the expected shape or units."""


def parse_series_key(
    key: str, variables: list[str], models: list[str]
) -> tuple[str, int, str] | None:
    """Split an hourly series name into ``(variable, member, model)``.

    Returns ``None`` for series that do not belong to a requested variable.
    """
    for variable in sorted(variables, key=len, reverse=True):
        if key != variable and not key.startswith(variable + "_"):
            continue
        match = _SUFFIX.match(key[len(variable) :])
        if match is None:
            continue
        member = int(match["member"] or 0)
        suffix = match["model"]
        if suffix is None:
            if len(models) != 1:
                continue
            model = models[0]
        else:
            matched = next((m for m in models if suffix == m or suffix.startswith(m + "_")), None)
            if matched is None:
                continue
            model = matched
        return variable, member, model
    return None


def _location_frame(
    location: dict[str, Any],
    *,
    station_id: str,
    band: str,
    elevation: int,
    variables: list[str],
    models: list[str],
) -> pl.DataFrame:
    hourly: dict[str, list[Any]] = location.get("hourly") or {}
    units: dict[str, str] = location.get("hourly_units") or {}
    times = hourly.get("time")
    if not times:
        raise OpenMeteoParseError(f"{station_id}/{band}: response has no hourly time axis")

    series: dict[tuple[str, int], dict[str, list[Any]]] = {}
    for key, values in hourly.items():
        if key == "time":
            continue
        parsed = parse_series_key(key, variables, models)
        if parsed is None:
            continue
        variable, member, model = parsed
        column, expected_unit = VARIABLES[variable]
        unit = units.get(key, expected_unit)
        if unit != expected_unit and unit not in _NO_DATA_UNITS:
            raise OpenMeteoParseError(
                f"{station_id}/{band}: '{key}' is in '{unit}', expected '{expected_unit}'"
            )
        series.setdefault((model, member), {})[column] = values

    frames = [
        pl.DataFrame(
            {"time_utc": times, **columns}, strict=False, infer_schema_length=None
        ).with_columns(model=pl.lit(model), member=pl.lit(member))
        for (model, member), columns in sorted(series.items())
    ]
    if not frames:
        raise OpenMeteoParseError(f"{station_id}/{band}: no requested variable in response")
    frame = pl.concat(frames, how="diagonal_relaxed")
    return frame.with_columns(
        station_id=pl.lit(station_id),
        band=pl.lit(band),
        elevation_m=pl.lit(elevation),
        time_utc=pl.col("time_utc").str.to_datetime("%Y-%m-%dT%H:%M", time_zone="UTC"),
    )


def parse_batch(batch: BronzeBatch) -> pl.DataFrame:
    """Tidy table with one row per station, band, model, member and hour."""
    frames: list[pl.DataFrame] = []
    for record in batch.records:
        context = record.context
        bands: list[str] = context["bands"]
        elevations: list[int] = context["elevations"]
        variables: list[str] = context["hourly"]
        models: list[str] = context["models"]
        unsupported = sorted(set(variables) - VARIABLES.keys())
        if unsupported:
            raise OpenMeteoParseError(
                f"unsupported Open-Meteo variable(s) {unsupported}; add them to VARIABLES"
            )
        locations = record.payload if isinstance(record.payload, list) else [record.payload]
        if len(locations) != len(bands):
            raise OpenMeteoParseError(
                f"{record.station_id}: expected {len(bands)} locations, got {len(locations)}"
            )
        for location, band, elevation in zip(locations, bands, elevations, strict=True):
            frames.append(
                _location_frame(
                    location,
                    station_id=record.station_id or "",
                    band=band,
                    elevation=elevation,
                    variables=variables,
                    models=models,
                )
            )
    if not frames:
        return pl.DataFrame(schema=SCHEMA)
    return pl.concat(frames, how="diagonal_relaxed")
