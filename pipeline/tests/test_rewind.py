"""Rewind: season archive -> committed hourly file -> historical KPIs -> committed payload."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from urllib.parse import parse_qs

import httpx
import polars as pl
import pytest

from bluebird_pipeline.bronze._season_points import station_points
from bluebird_pipeline.cli import main
from bluebird_pipeline.config import Config, Rewind
from bluebird_pipeline.context import RunContext
from bluebird_pipeline.diamond.models import DiamondRewind
from bluebird_pipeline.geo import distance_m, offset
from bluebird_pipeline.rewind import is_over, load_season, run_rewind
from bluebird_pipeline.storage import LocalStorage

# Three local days (Europe/Paris, UTC+1): 72 hours.
SHORT = {"start": date(2026, 1, 1), "end": date(2026, 1, 3)}
ALPHA = [0.1, 42.8]


def _rewind(config: Config) -> Rewind:
    return config.rewind("2025-26").model_copy(update=SHORT)


def _piste(station_id: str, osm_id: int, line: list[list[float]]) -> dict[str, object]:
    return {
        "station_id": station_id,
        "osm_id": osm_id,
        "feature": "piste",
        "kind": "easy",
        "name": None,
        "length_m": 0.0,
        "coordinates": line,
    }


@pytest.fixture
def features() -> pl.DataFrame:
    """Two pistes of Alpha going north from the station; Beta has none."""
    north = offset(ALPHA, 1000, 0)
    east = offset(north, 500, 90)
    return pl.DataFrame([_piste("alpha", 1, [ALPHA, north]), _piste("alpha", 2, [north, east])])


def _transport(calls: list[dict[str, str]], depth_m: float = 0.8) -> httpx.MockTransport:
    """Archive API, answering only the requested variables.

    Alpha gets 0.2 cm/h from 00:00 to 05:00 UTC and ``depth_m`` of snow on the
    ground; Beta 0.5 cm/h from 00:00 to 02:00 and 0.5 m.
    """

    def handler(request: httpx.Request) -> httpx.Response:
        query = {k: v[0] for k, v in parse_qs(request.url.query.decode()).items()}
        calls.append(query)
        start = datetime.fromisoformat(query["start_date"]).replace(tzinfo=UTC)
        end = datetime.fromisoformat(query["end_date"]).replace(tzinfo=UTC) + timedelta(days=1)
        times = [
            start + timedelta(hours=h) for h in range(int((end - start).total_seconds()) // 3600)
        ]
        lats = query["latitude"].split(",")
        alpha = lats[0].startswith("42.8")
        rate, hours, depth = (0.2, 6, depth_m) if alpha else (0.5, 3, 0.5)
        series = {
            "snowfall": ("cm", [rate if t.hour < hours else 0.0 for t in times]),
            "sunshine_duration": ("s", [0.0 if t.hour < hours else 3600.0 for t in times]),
            "cloud_cover": ("%", [100 if t.hour < hours else 0 for t in times]),
            "weather_code": ("wmo code", [73 if t.hour < hours else 0 for t in times]),
            "snow_depth": ("m", [depth for _ in times]),
            # Alpha's slopes sit in the cloud from 10:00 to 16:00 UTC: white days.
            "relative_humidity_2m": (
                "%",
                [100 if alpha and 9 <= t.hour < 16 else 70 for t in times],
            ),
            "cloud_cover_low": ("%", [100 if alpha and 9 <= t.hour < 16 else 0 for t in times]),
            "shortwave_radiation": ("W/m²", [300.0 for _ in times]),
        }
        wanted = query["hourly"].split(",")
        location = {
            "elevation": 1800.0,
            "hourly_units": {"time": "iso8601", **{v: series[v][0] for v in wanted}},
            "hourly": {
                "time": [t.strftime("%Y-%m-%dT%H:%M") for t in times],
                **{v: series[v][1] for v in wanted},
            },
        }
        body = location if len(lats) == 1 else [location for _ in lats]
        return httpx.Response(200, json=body)

    return httpx.MockTransport(handler)


@pytest.fixture
def rewind_ctx(two_station_config: Config, storage: LocalStorage, features: pl.DataFrame):
    rewind = _rewind(two_station_config)
    config = two_station_config
    sources = [
        s.model_copy(update={"params": {**s.params, "min_interval_s": 0}})
        if s.schedule == "season"
        else s
        for s in config.sources
    ]
    config = Config(**{**config.__dict__, "sources": sources})
    ctx = RunContext.create(
        config,
        storage,
        massif_ids=["pyrenees"],
        rewind=rewind,
        now=datetime(2026, 10, 4, 8, 0, tzinfo=UTC),
    )
    ctx._reference_cache["domain_features"] = features
    return ctx


# -- points ---------------------------------------------------------------------


def test_points_follow_the_pistes_and_ring_the_domain(rewind_ctx: RunContext, features) -> None:
    alpha = next(r for r in rewind_ctx.stations() if r.id == "alpha")
    points = station_points(alpha, features, domain_points=4, offpiste_points=8)
    assert points == station_points(alpha, features, domain_points=4, offpiste_points=8)
    kinds = [p.kind for p in points]
    assert kinds == ["station"] + ["domain"] * 4 + ["offpiste"] * 8
    assert points[0].elevation == 2000  # mid band of Alpha
    assert all(p.elevation is None for p in points[1:])
    # 1.5 km of pistes, 4 points: 187.5 m, 562.5 m, 937.5 m along the first, 1312.5 m on the second.
    assert distance_m(ALPHA, [points[1].lon, points[1].lat]) == pytest.approx(187.5, abs=15)
    ring = [distance_m(ALPHA, [p.lon, p.lat]) for p in points[5:]]
    assert min(ring) > 800  # beyond the farthest piste vertex plus the margin, from the centre


def test_a_station_without_pistes_only_has_its_own_point(rewind_ctx: RunContext, features) -> None:
    beta = next(r for r in rewind_ctx.stations() if r.id == "beta")
    assert [p.kind for p in station_points(beta, features)] == ["station"]


# -- full run -------------------------------------------------------------------


def test_rewind_writes_the_hourly_file_and_the_rankings(rewind_ctx: RunContext) -> None:
    calls: list[dict[str, str]] = []
    report = run_rewind(rewind_ctx, http=httpx.Client(transport=_transport(calls)))
    assert report.errors == []

    # Per source (AROME snow, ICON depth, AROME light): Alpha's station point and area
    # points, Beta's point.
    assert len(calls) == 9
    assert calls[0]["start_date"] == "2025-12-31" and calls[0]["end_date"] == "2026-01-04"
    assert calls[0]["elevation"] == "2000" and "elevation" not in calls[1]
    assert len(calls[1]["latitude"].split(",")) == 16  # 8 domain + 8 off-piste
    assert calls[3]["models"] == "icon_seamless" and calls[3]["hourly"] == "snow_depth"
    assert len(calls[4]["latitude"].split(",")) == 8  # domain only

    root = rewind_ctx.config.root
    hourly = load_season(rewind_ctx.config, rewind_ctx.rewind, ["pyrenees"])
    assert hourly is not None
    assert set(hourly["point_kind"]) == {"station", "domain", "offpiste"}
    assert hourly.schema["snowfall_cm"] == pl.Float32

    payload = DiamondRewind.model_validate_json(
        (root / "rewind/2025-26/pyrenees.json").read_text(encoding="utf-8")
    )
    assert payload.start == SHORT["start"] and payload.end == SHORT["end"]
    total = payload.kpis["season_total_snowfall"]
    assert total.unit == "m"  # computed in cm, published in metres
    # 3 days x 6 h x 0.2 cm for Alpha, 3 days x 3 h x 0.5 cm for Beta.
    assert [(e.station_id, e.value) for e in total.ranking] == [("beta", 0.045), ("alpha", 0.036)]
    longest = payload.kpis["season_longest_snowfall"].ranking
    assert [(e.station_id, e.value) for e in longest] == [("alpha", 6.0), ("beta", 3.0)]
    assert longest[0].drivers["start"] == "2026-01-01T00:00:00+01:00"  # first snowy hour
    domain = payload.kpis["season_domain_snowfall"].ranking
    assert [(e.station_id, e.value, e.drivers["points"]) for e in domain] == [("alpha", 0.036, 8)]
    assert "season_offpiste_snowfall" in payload.kpis
    # Alpha keeps 0.8 m on its slopes all season: 100 % of the days above 70 cm.
    deep = payload.kpis["season_deep_snow_days"]
    assert deep.unit == "%"
    assert [(e.station_id, e.value) for e in deep.ranking] == [("alpha", 100.0)]
    # Alpha's slopes are in the cloud 7 of the 8 ski hours every day: 3 white days.
    white = payload.kpis["season_white_days"]
    assert [(e.station_id, e.value) for e in white.ranking] == [("alpha", 3.0)]
    assert white.ranking[0].drivers == {"days": 3, "white_share_pct": 100}
    assert {s.id for s in payload.sources} == {
        "open_meteo_historical",
        "open_meteo_historical_snowpack",
        "open_meteo_historical_light",
        "osm_overpass",
    }


def test_no_fetch_recomputes_the_same_rankings_from_the_committed_file(
    rewind_ctx: RunContext,
) -> None:
    run_rewind(rewind_ctx, http=httpx.Client(transport=_transport([])))
    path = rewind_ctx.config.root / "rewind/2025-26/pyrenees.json"
    first = json.loads(path.read_text(encoding="utf-8"))
    season = (rewind_ctx.config.root / "rewind/2025-26/pyrenees.hourly.parquet").read_bytes()

    def boom(request: httpx.Request) -> httpx.Response:
        raise AssertionError("no network call expected")

    report = run_rewind(
        rewind_ctx, fetch=False, http=httpx.Client(transport=httpx.MockTransport(boom))
    )
    assert report.errors == []
    again = json.loads(path.read_text(encoding="utf-8"))
    assert {**again, "generated_at": None} == {**first, "generated_at": None}
    assert (
        rewind_ctx.config.root / "rewind/2025-26/pyrenees.hourly.parquet"
    ).read_bytes() == season


def test_fetching_one_source_keeps_the_other_sources_rows(rewind_ctx: RunContext) -> None:
    run_rewind(rewind_ctx, http=httpx.Client(transport=_transport([])))
    calls: list[dict[str, str]] = []
    report = run_rewind(
        rewind_ctx,
        only=["open_meteo_historical_snowpack"],
        http=httpx.Client(transport=_transport(calls, depth_m=0.4)),
    )
    assert report.errors == []
    assert {c["models"] for c in calls} == {"icon_seamless"}
    hourly = load_season(rewind_ctx.config, rewind_ctx.rewind, ["pyrenees"])
    assert hourly is not None
    assert set(hourly["model"]) == {"meteofrance_seamless", "icon_seamless"}
    payload = DiamondRewind.model_validate_json(
        (rewind_ctx.config.root / "rewind/2025-26/pyrenees.json").read_text(encoding="utf-8")
    )
    assert payload.kpis["season_deep_snow_days"].ranking[0].value == 0.0  # 40 cm now
    assert payload.kpis["season_total_snowfall"].ranking[0].value == 0.045  # AROME rows kept


# -- guards ---------------------------------------------------------------------


def test_a_season_is_only_reviewed_once_over(repo_config: Config) -> None:
    rewind = repo_config.rewind("2025-26")
    assert not is_over(rewind, date(2026, 5, 1))
    assert is_over(rewind, date(2026, 5, 2))


def test_daily_run_refuses_season_sources(tmp_path: Path) -> None:
    code = main(["run", "--source", "open_meteo_historical", "--data-dir", str(tmp_path)])
    assert code == 2


def test_daily_runs_ignore_historical_kpis(repo_config: Config) -> None:
    live = {k.id for k in repo_config.enabled_kpis(kind="live")}
    assert live and not live & {"season_total_snowfall", "season_domain_snowfall"}
