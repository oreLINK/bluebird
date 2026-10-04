"""Demo data for frontend development (``bluebird demo``).

Runs the real pipeline (every layer) against a mocked Open-Meteo that returns
synthetic but plausible winter weather: a snowstorm overnight, heavier on the
Atlantic (western) side, windier in the east, with member-to-member spread.
The diamond output is copied to ``web/public/data`` so ``npm run dev`` shows a
realistic page without network access. Regenerate it whenever the diamond
schema changes.
"""

from __future__ import annotations

import hashlib
import math
import shutil
import tempfile
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs

import httpx

from .config import Config
from .context import RunContext
from .runner import LAYERS, RunReport, run_pipeline
from .storage import LocalStorage

DEMO_DATE = date(2027, 1, 15)
_STORM_PEAK = datetime(2027, 1, 15, 2, tzinfo=UTC)

# Open-Meteo series suffix and perturbed member count per requested model.
_ENSEMBLE_MODELS = {
    "ecmwf_ifs025": ("ecmwf_ifs025_ensemble", 50),
    "icon_seamless": ("icon_seamless_eps", 39),
}
_UNITS = {
    "snowfall": "cm",
    "precipitation": "mm",
    "rain": "mm",
    "temperature_2m": "°C",
    "wind_speed_10m": "km/h",
    "wind_gusts_10m": "km/h",
    "freezing_level_height": "m",
    "cloud_cover": "%",
    "cloud_cover_low": "%",
    "relative_humidity_2m": "%",
    "shortwave_radiation": "W/m²",
}


def _noise(*parts: object) -> float:
    """Deterministic pseudo-random number in [0, 1)."""
    digest = hashlib.sha256("|".join(map(str, parts)).encode()).digest()
    return int.from_bytes(digest[:8], "big") / 2**64


def demo_value(
    variable: str, model: str, member: int, when: datetime, lon: float, elevation: int
) -> float | None:
    """Synthetic hourly value for one location, model member and time."""
    west = min(1.0, max(0.0, (2.1 - lon) / 2.9))  # 1 = Atlantic side
    spread = 0.2 + 1.6 * _noise(model, member, round(lon, 3))
    altitude = min(1.3, max(0.5, 0.6 + (elevation - 1500) / 1500))
    hours_from_peak = (when - _STORM_PEAK).total_seconds() / 3600
    storm = max(0.0, 1 - abs(hours_from_peak) / 11)
    showers = 0.0
    if (
        when.date() == DEMO_DATE
        and 8 <= when.hour <= 15
        and _noise(model, member, lon, "sh") > 0.45
    ):
        showers = 0.12 + 0.25 * west

    snowfall = (0.1 + 1.0 * west) * storm * spread * altitude + showers * spread
    wind = 8 + 55 * (1 - west) * _noise(model, member, lon, "wind") * (0.6 + 0.4 * storm)
    temperature = (
        -2.0 - (elevation - 1500) / 170 + 4 * (1 - west) * _noise(model, member, lon, "temp")
    )
    values: dict[str, float | None] = {
        "snowfall": round(snowfall, 2),
        "precipitation": round(snowfall * 0.7, 2),
        "rain": 0.0,
        "temperature_2m": round(temperature, 1),
        "wind_speed_10m": round(wind, 1),
        "wind_gusts_10m": round(wind * 1.6, 1),
        "freezing_level_height": round(1200 + 600 * (1 - west), 0),
        "cloud_cover": round(100 * storm, 0),
        "cloud_cover_low": round(100 * storm * (0.4 + 0.6 * west), 0),
        "relative_humidity_2m": round(min(100.0, 72 + 30 * storm * (0.5 + west)), 0),
        # Daylight (~07:00-17:00 UTC in winter), dimmed by the storm.
        "shortwave_radiation": round(
            max(0.0, math.sin(math.pi * (when.hour - 7) / 10)) * 420 * (1 - 0.85 * storm), 1
        ),
    }
    return values.get(variable)


def _location(query: dict[str, str], lon: float, elevation: int, ensemble: bool) -> dict[str, Any]:
    past_days = int(query.get("past_days", 0))
    days = past_days + int(query.get("forecast_days", 1))
    start = datetime.combine(DEMO_DATE - timedelta(days=past_days), datetime.min.time(), UTC)
    times = [start + timedelta(hours=h) for h in range(days * 24)]
    models = query["models"].split(",")
    variables = query["hourly"].split(",")
    hourly: dict[str, list[Any]] = {"time": [t.strftime("%Y-%m-%dT%H:%M") for t in times]}
    units = {"time": "iso8601"}
    for model in models:
        suffix, perturbed = _ENSEMBLE_MODELS.get(model, (model, 0))
        for member in range(perturbed + 1 if ensemble else 1):
            for variable in variables:
                key = variable + (f"_member{member:02d}" if member else "")
                key += f"_{suffix}" if len(models) > 1 else ""
                hourly[key] = [
                    demo_value(variable, model, member, t, lon, elevation) for t in times
                ]
                units[key] = _UNITS[variable]
    return {"elevation": float(elevation), "hourly_units": units, "hourly": hourly}


def demo_transport() -> httpx.MockTransport:
    """Mocked Open-Meteo forecast and ensemble APIs serving :func:`demo_value`."""

    def handler(request: httpx.Request) -> httpx.Response:
        query = {k: v[0] for k, v in parse_qs(request.url.query.decode()).items()}
        lons = [float(v) for v in query["longitude"].split(",")]
        elevations = [int(v) for v in query["elevation"].split(",")]
        ensemble = "ensemble" in request.url.host
        payload = [
            _location(query, lon, e, ensemble) for lon, e in zip(lons, elevations, strict=True)
        ]
        return httpx.Response(200, json=payload if len(payload) > 1 else payload[0])

    return httpx.MockTransport(handler)


def build_demo(config: Config, out_dir: Path) -> RunReport:
    """Run every layer on synthetic weather and copy the diamond output to ``out_dir``."""
    sources = [
        s.model_copy(update={"params": {**s.params, "min_interval_s": 0}})
        for s in config.enabled_sources(schedule="daily")
        if s.extractor.startswith("open_meteo")
    ]
    with tempfile.TemporaryDirectory() as tmp:
        storage = LocalStorage(Path(tmp))
        ctx = RunContext.create(
            config,
            storage,
            run_date=DEMO_DATE,
            now=datetime(2027, 1, 15, 4, 32, tzinfo=UTC),
        )
        with httpx.Client(transport=demo_transport()) as http:
            report = run_pipeline(ctx, list(LAYERS), sources, http=http)
        target = out_dir / "diamond"
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(Path(tmp) / "diamond", target)
    return report
