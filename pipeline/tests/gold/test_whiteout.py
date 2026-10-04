"""White days: clear-sky radiation, white hour rule, live probability."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import polars as pl
import pytest
from _factories import ensemble_frame
from pydantic import ValidationError

from bluebird_pipeline.context import RunContext
from bluebird_pipeline.gold import AGGREGATORS
from bluebird_pipeline.gold._whiteout import (
    WhiteoutRule,
    clear_sky_expr,
    clear_sky_ghi,
    white_hour_expr,
)
from bluebird_pipeline.rewind import merge_columns

NOON = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)


def test_clear_sky_radiation_follows_the_sun() -> None:
    noon = clear_sky_ghi(NOON - timedelta(minutes=30), 42.9, 0.1)
    assert 330 < noon < 450  # low winter sun in the Pyrenees
    assert clear_sky_ghi(datetime(2026, 1, 15, 2, tzinfo=UTC), 42.9, 0.1) == 0.0
    june = clear_sky_ghi(datetime(2026, 6, 21, 11, 30, tzinfo=UTC), 42.9, 0.1)
    assert june > 2 * noon
    frame = pl.DataFrame({"time_utc": [NOON]}).with_columns(
        pl.col("time_utc").dt.replace_time_zone("UTC")
    )
    value = frame.select(clear_sky_expr("time_utc", 42.9, 0.1)).item()
    assert value == pytest.approx(noon, rel=1e-3)  # the hour ending at noon


@pytest.mark.parametrize(
    ("row", "white"),
    [
        ({"relative_humidity_pct": 99, "cloud_cover_low_pct": 95}, True),  # in the cloud
        ({"relative_humidity_pct": 99, "cloud_cover_low_pct": None, "cloud_cover_pct": 95}, True),
        ({"relative_humidity_pct": 90, "cloud_cover_low_pct": 95}, False),
        ({"snowfall_cm": 0.8}, True),  # steady snowfall
        ({"shortwave_wm2": 60.0}, True),  # flat light: 60 < 0.3 x ~390
        ({"shortwave_wm2": 300.0}, False),
    ],
)
def test_white_hour_rule(row: dict[str, float | None], white: bool) -> None:
    base = {
        "time_utc": NOON,
        "relative_humidity_pct": 70.0,
        "cloud_cover_low_pct": 0.0,
        "cloud_cover_pct": 0.0,
        "snowfall_cm": 0.0,
        "shortwave_wm2": 300.0,
    }
    frame = pl.DataFrame([{**base, **row}], schema_overrides={"cloud_cover_low_pct": pl.Float64})
    rule = WhiteoutRule()
    result = frame.select(white_hour_expr(rule, clear_sky_expr("time_utc", 42.9, 0.1))).item()
    assert result is white


def test_rule_checks_its_window() -> None:
    with pytest.raises(ValidationError, match="ski_end must be after"):
        WhiteoutRule(ski_start="17:00", ski_end="09:00")
    with pytest.raises(ValidationError, match="exceeds the ski hours"):
        WhiteoutRule(min_white_hours=9)


def test_whiteout_chance_is_the_share_of_white_scenarios(ctx: RunContext) -> None:
    # Run date 2026-12-14 (Europe/Paris): ski hours end 09:00-16:00 UTC. Members 0-3 are
    # in the cloud all day, members 4-9 in the clear.
    start = datetime(2026, 12, 14, 0, tzinfo=UTC)

    def values(station: str, member: int, when: datetime) -> dict[str, float]:
        cloudy = member < 4
        return {
            "relative_humidity_pct": 100.0 if cloudy else 60.0,
            "cloud_cover_low_pct": 100.0 if cloudy else 0.0,
            "cloud_cover_pct": 100.0 if cloudy else 0.0,
            "shortwave_wm2": 400.0,
        }

    frame = ensemble_frame(
        stations=["alpha", "beta"], bands=["mid"], members=10, start=start, hours=48, values=values
    )
    ctx._silver_cache["ensemble_hourly"] = frame
    kpi = next(k for k in ctx.config.kpis if k.id == "whiteout_chance_today")
    results = AGGREGATORS.get(kpi.aggregator)(kpi).aggregate(ctx)
    assert {r.station_id: r.probability for r in results} == {"alpha": 0.4, "beta": 0.4}
    assert results[0].members == 10

    tomorrow = next(k for k in ctx.config.kpis if k.id == "whiteout_chance_tomorrow")
    later = AGGREGATORS.get(tomorrow.aggregator)(tomorrow).aggregate(ctx)
    assert {r.window_start.date().isoformat() for r in later} == {"2026-12-15"}


def test_merge_by_column_keeps_the_other_columns_of_the_same_model() -> None:
    key = {"station_id": "a", "point_id": "domain-1", "model": "m", "time_utc": NOON}
    meta = {"point_kind": "domain", "lat": 42.9, "lon": 0.1, "elevation_m": 1800}
    existing = pl.DataFrame([{**key, **meta, "snowfall_cm": 1.5, "shortwave_wm2": None}])
    new = pl.DataFrame([{**key, **meta, "snowfall_cm": None, "shortwave_wm2": 250.0}])
    merged = merge_columns(existing, new, ["shortwave_wm2"])
    assert merged.select("snowfall_cm", "shortwave_wm2").row(0) == (1.5, 250.0)
    assert merged.height == 1
