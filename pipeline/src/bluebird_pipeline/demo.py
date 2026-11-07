"""Demo data for frontend development (``bluebird demo``).

Runs the real pipeline (every layer) against a mocked Open-Meteo that returns
synthetic but plausible winter weather: a snowstorm overnight, heavier on the
Atlantic (western) side, windier in the east, with member-to-member spread,
then a second, weaker episode the next evening. The diamond output (payloads,
status, manifest) is copied to ``web/public/data`` so ``npm run dev`` shows a
realistic page without network access. Regenerate it whenever the diamond
schema changes.

``now`` picks the refresh to simulate (default: the 06:00 one); e.g. 17:07 UTC
shows what the page looks like after the 18:00 refresh.

The avalanche bulletins need a Météo-France API key, so the demo does not
fetch them: :func:`write_demo_bulletins` writes synthetic ones to silver
between the silver and gold layers (:func:`run_demo_pipeline`), issued at
16:00 local the day before they are valid, each with its day-after trend, so
tomorrow first shows the trend, then its own bulletin after the afternoon.
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
import polars as pl

from .config import Config, Source
from .context import RunContext
from .runner import RunReport, finalize, run_pipeline
from .silver._avalanche import AVALANCHE_DATASET, AVALANCHE_SCHEMA
from .storage import LocalStorage, silver_key

DEMO_DATE = date(2027, 1, 15)
DEMO_NOW = datetime(2027, 1, 15, 5, 7, tzinfo=UTC)  # the 06:00 refresh, Paris time
_STORM_PEAK = datetime(2027, 1, 15, 2, tzinfo=UTC)
_SECOND_PEAK = datetime(2027, 1, 16, 21, tzinfo=UTC)

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
    hours_from_second = (when - _SECOND_PEAK).total_seconds() / 3600
    storm = max(storm, 0.45 * max(0.0, 1 - abs(hours_from_second) / 6))
    showers = 0.0
    if (
        when.date() == DEMO_DATE
        and 8 <= when.hour <= 15
        and _noise(model, member, lon, "sh") > 0.45
    ):
        showers = 0.12 + 0.25 * west

    snowfall = (0.1 + 1.0 * west) * storm * spread * altitude + showers * spread
    wind = 8 + 55 * (1 - west) * _noise(model, member, lon, "wind") * (0.6 + 0.4 * storm)
    # Day/night cycle: up to +7 °C in the early afternoon (13:00 UTC), -2 °C at night,
    # so the thaw, refreeze and mild-day KPIs have something to show.
    daytime = math.sin(math.pi * (when.hour - 8) / 10)
    temperature = (
        -2.0
        - (elevation - 1500) / 170
        + 4 * (1 - west) * _noise(model, member, lon, "temp")
        + (7.0 * daytime if daytime > 0 else -2.0)
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


def _location(
    query: dict[str, str], lon: float, elevation: int, ensemble: bool, today: date
) -> dict[str, Any]:
    past_days = int(query.get("past_days", 0))
    days = past_days + int(query.get("forecast_days", 1))
    start = datetime.combine(today - timedelta(days=past_days), datetime.min.time(), UTC)
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


def demo_transport(today: date = DEMO_DATE) -> httpx.MockTransport:
    """Mocked Open-Meteo forecast and ensemble APIs serving :func:`demo_value`.

    Like the real API, hourly series start at 00:00 UTC ``past_days`` before
    ``today`` (the UTC date of the request).
    """

    def handler(request: httpx.Request) -> httpx.Response:
        query = {k: v[0] for k, v in parse_qs(request.url.query.decode()).items()}
        lons = [float(v) for v in query["longitude"].split(",")]
        elevations = [int(v) for v in query["elevation"].split(",")]
        ensemble = "ensemble" in request.url.host
        payload = [
            _location(query, lon, e, ensemble, today)
            for lon, e in zip(lons, elevations, strict=True)
        ]
        return httpx.Response(200, json=payload if len(payload) > 1 else payload[0])

    return httpx.MockTransport(handler)


# Synthetic avalanche bulletins per Météo-France massif number: (name, level below
# the altitude limit, level above it, altitude limit or None) for today; tomorrow
# the danger rises by one on the Atlantic side (massifs up to 66), capped at 5.
_DEMO_BULLETINS: dict[int, tuple[str, int, int, int | None]] = {
    64: ("Pays-Basque", 3, 3, None),
    65: ("Aspe Ossau", 3, 4, 1800),
    66: ("Haute-Bigorre", 3, 4, 2000),
    67: ("Aure Louron", 3, 3, None),
    68: ("Luchonnais", 2, 3, 2000),
    69: ("Couserans", 2, 2, None),
    70: ("Haute-Ariège", 2, 2, None),
    71: ("Andorre", 2, 2, None),
    72: ("Orlu St-Barthélemy", 2, 2, None),
    73: ("Capcir Puymorens", 1, 2, 2300),
    74: ("Cerdagne Canigou", 1, 1, None),
}


def _demo_levels(number: int, offset: int) -> tuple[str, int, int, int | None]:
    name, low, high, limit = _DEMO_BULLETINS[number]
    rise = 1 if offset and number <= 66 else 0
    return name, min(5, low + rise), min(5, high + rise), limit


def demo_bulletins(ctx: RunContext) -> pl.DataFrame:
    """Bulletins (and their day-after trends) already issued at ``ctx.generated_at``."""
    tz = ctx.massifs()[0].tz
    rows = []
    for offset in (0, 1):
        valid = ctx.run_date + timedelta(days=offset)
        issued = datetime.combine(valid - timedelta(days=1), datetime.min.time(), tz)
        issued = (issued + timedelta(hours=16)).astimezone(UTC)
        if issued > ctx.generated_at:
            continue
        for number in _DEMO_BULLETINS:
            name, low, high, limit = _demo_levels(number, offset)
            _, _, trend, _ = _demo_levels(number, offset + 1)
            common = {"massif_number": number, "massif_name": name, "issued_at": issued}
            rows.append(
                {
                    **common,
                    "valid_date": valid,
                    "level_low": low,
                    "level_high": high,
                    "altitude_limit_m": limit,
                    "trend": False,
                }
            )
            rows.append(
                {
                    **common,
                    "valid_date": valid + timedelta(days=1),
                    "level_low": trend,
                    "level_high": trend,
                    "altitude_limit_m": None,
                    "trend": True,
                }
            )
    return pl.DataFrame(rows, schema=AVALANCHE_SCHEMA)


def write_demo_bulletins(ctx: RunContext) -> str:
    """Write :func:`demo_bulletins` as this run's ``avalanche_bulletin`` silver table."""
    key = silver_key(AVALANCHE_DATASET, ctx.run_date, ctx.run_id)
    ctx.storage.write_parquet(key, demo_bulletins(ctx))
    return key


def run_demo_pipeline(
    ctx: RunContext, sources: list[Source], http: httpx.Client | None = None
) -> RunReport:
    """Every layer, with the demo avalanche bulletins written between silver and gold."""
    report = run_pipeline(ctx, ["bronze", "silver"], sources, http=http, final=False)
    report.wrote(write_demo_bulletins(ctx))
    report.step("bronze", "meteofrance_bra", "ok", message="synthetic demo bulletins")
    report.step("silver", "meteofrance_bra", "ok", message="synthetic demo bulletins")
    later = run_pipeline(ctx, ["gold", "diamond"], [], final=False)
    report.written += later.written
    report.errors += later.errors
    report.steps += later.steps
    finalize(ctx, report)
    return report


def build_demo(config: Config, out_dir: Path, now: datetime = DEMO_NOW) -> RunReport:
    """Run every layer on synthetic weather and copy the diamond output to ``out_dir``."""
    sources = [
        s.model_copy(update={"params": {**s.params, "min_interval_s": 0}})
        for s in config.enabled_sources(schedule="daily")
        if s.extractor.startswith("open_meteo")
    ]
    with tempfile.TemporaryDirectory() as tmp:
        storage = LocalStorage(Path(tmp))
        ctx = RunContext.create(config, storage, now=now)
        with httpx.Client(transport=demo_transport(now.astimezone(UTC).date())) as http:
            report = run_demo_pipeline(ctx, sources, http=http)
        target = out_dir / "diamond"
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(Path(tmp) / "diamond", target)
    return report
