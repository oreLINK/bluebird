"""Test data builders shared by the test suite.

Open-Meteo payloads are synthesised with the exact series naming of the real
API (verified against live responses), so parsing is exercised realistically
without network access.
"""

from __future__ import annotations

import re
import shutil
from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs

import httpx
import polars as pl

from bluebird_pipeline.paths import repo_root

RUN_DATE = date(2026, 12, 14)  # winter: Europe/Paris is UTC+1

# requested model id -> (series suffix used by the API, number of perturbed members)
ENSEMBLE_MODELS: dict[str, tuple[str, int]] = {
    "ecmwf_ifs025": ("ecmwf_ifs025_ensemble", 50),
    "icon_seamless": ("icon_seamless_eps", 39),
}
UNITS = {
    "snowfall": "cm",
    "precipitation": "mm",
    "rain": "mm",
    "temperature_2m": "°C",
    "wind_speed_10m": "km/h",
    "wind_gusts_10m": "km/h",
    "freezing_level_height": "undefined",
    "cloud_cover": "%",
}

# value(variable, model, member, time_utc, elevation) -> value
ValueFn = Callable[[str, str, int, datetime, int], float | None]


def default_values(variable: str, model: str, member: int, when: datetime, elevation: int) -> float:
    """Light snow every hour, cold, calm: a deterministic, plausible winter day."""
    return {
        "snowfall": 0.4,
        "precipitation": 0.3,
        "rain": 0.0,
        "temperature_2m": -4.0,
        "wind_speed_10m": 15.0,
        "wind_gusts_10m": 25.0,
        "cloud_cover": 90.0,
    }.get(variable, 0.0)


def hourly_times(start_day: date, days: int) -> list[datetime]:
    start = datetime(start_day.year, start_day.month, start_day.day, tzinfo=UTC)
    return [start + timedelta(hours=h) for h in range(days * 24)]


def open_meteo_location(
    *,
    times: list[datetime],
    elevation: int,
    variables: list[str],
    models: list[str],
    ensemble: bool,
    values: ValueFn = default_values,
) -> dict[str, Any]:
    """One location of an Open-Meteo response with real series naming."""
    hourly: dict[str, list[Any]] = {"time": [t.strftime("%Y-%m-%dT%H:%M") for t in times]}
    units: dict[str, str] = {"time": "iso8601"}
    multi = len(models) > 1
    for model in models:
        suffix, perturbed = ENSEMBLE_MODELS.get(model, (model, 0))
        members = range(perturbed + 1) if ensemble else range(1)
        for member in members:
            for variable in variables:
                key = variable
                if member:
                    key += f"_member{member:02d}"
                if multi:
                    key += f"_{suffix}"
                hourly[key] = [values(variable, model, member, t, elevation) for t in times]
                units[key] = UNITS[variable]
    return {"elevation": float(elevation), "hourly_units": units, "hourly": hourly}


def open_meteo_transport(values: ValueFn = default_values) -> httpx.MockTransport:
    """Mock both Open-Meteo APIs, answering from the query parameters."""

    def handler(request: httpx.Request) -> httpx.Response:
        query = {k: v[0] for k, v in parse_qs(request.url.query.decode()).items()}
        past_days = int(query.get("past_days", 0))
        days = past_days + int(query.get("forecast_days", 1))
        times = hourly_times(RUN_DATE - timedelta(days=past_days), days)
        payload = [
            open_meteo_location(
                times=times,
                elevation=int(elevation),
                variables=query["hourly"].split(","),
                models=query["models"].split(","),
                ensemble="ensemble" in request.url.host,
                values=values,
            )
            for elevation in query["elevation"].split(",")
        ]
        return httpx.Response(200, json=payload if len(payload) > 1 else payload[0])

    return httpx.MockTransport(handler)


def tiny_config_dir(tmp_path: Path, stations_yaml: str | None = None) -> Path:
    """Copy of the repository config, optionally with a smaller Pyrenees station list."""
    target = tmp_path / "config"
    shutil.copytree(repo_root() / "config", target)
    if stations_yaml is not None:
        (target / "stations" / "pyrenees.yaml").write_text(stations_yaml, encoding="utf-8")
    return target


TWO_STATIONS = """
defaults:
  grooming_end: "02:00"
  lifts_open: "09:00"
stations:
  - id: alpha
    name: Alpha
    lat: 42.8
    lon: 0.1
    elevation: { base: 1500, summit: 2500 }
  - id: beta
    name: Beta
    lat: 42.9
    lon: 0.2
    elevation: { base: 1400, summit: 2200 }
    grooming_end: "22:00"
"""


def ensemble_frame(
    *,
    stations: list[str],
    bands: list[str],
    members: int,
    start: datetime,
    hours: int,
    values: Callable[[str, int, datetime], dict[str, float | None]],
    model: str = "test_model",
) -> pl.DataFrame:
    """Silver ``ensemble_hourly`` table built directly (bypassing bronze)."""
    rows = []
    for station in stations:
        for band in bands:
            for member in range(members):
                for h in range(hours):
                    when = start + timedelta(hours=h)
                    rows.append(
                        {
                            "station_id": station,
                            "band": band,
                            "elevation_m": 2000,
                            "time_utc": when,
                            "model": model,
                            "member": member,
                            "snowfall_cm": 0.0,
                            "temperature_c": -5.0,
                            "wind_speed_kmh": 10.0,
                            **values(station, member, when),
                        }
                    )
    return pl.DataFrame(rows)


# ------------------------------------------------------------------ Overpass

_STATION_ORIGINS = {"alpha": (42.8, 0.1), "beta": (42.9, 0.2)}


def overpass_payload(station_id: str) -> dict[str, Any]:
    """Overpass `out tags geom` response: one piste, one lift, plus ignored elements."""
    lat, lon = _STATION_ORIGINS[station_id]
    offset = 0 if station_id == "alpha" else 100

    def line(d_lat: float) -> list[dict[str, float]]:
        return [{"lat": round(lat + d_lat * i / 2, 6), "lon": lon} for i in range(3)]

    return {
        "elements": [
            {
                "type": "way",
                "id": 1000 + offset,
                "tags": {"piste:type": "downhill", "piste:difficulty": "easy", "name": "Blue"},
                "geometry": line(0.002),
            },
            {
                "type": "way",
                "id": 2000 + offset,
                "tags": {"aerialway": "chair_lift", "name": "Chair"},
                "geometry": line(0.003),
            },
            {
                "type": "way",
                "id": 3000 + offset,
                "tags": {"aerialway": "station"},
                "geometry": line(0.0),
            },
            {"type": "node", "id": 4000 + offset, "lat": lat, "lon": lon},
        ]
    }


def overpass_transport(calls: list[str] | None = None) -> httpx.MockTransport:
    """Mock Overpass: answers each `around:` query with the matching station payload."""

    def handler(request: httpx.Request) -> httpx.Response:
        query = parse_qs(request.content.decode())["data"][0]
        match = re.search(r"around:\d+,([-\d.]+),([-\d.]+)", query)
        assert match, query
        lat = float(match.group(1))
        station_id = min(_STATION_ORIGINS, key=lambda s: abs(_STATION_ORIGINS[s][0] - lat))
        if calls is not None:
            calls.append(station_id)
        return httpx.Response(200, json=overpass_payload(station_id))

    return httpx.MockTransport(handler)
