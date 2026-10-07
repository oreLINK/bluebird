"""Bluebird day: fresh snow before the ski day, then a sunny ski day."""

from __future__ import annotations

from datetime import UTC, datetime

import polars as pl
import pytest
from _factories import ensemble_frame
from pydantic import ValidationError

from bluebird_pipeline.context import RunContext
from bluebird_pipeline.gold import AGGREGATORS
from bluebird_pipeline.gold._whiteout import clear_sky_expr, sunny_hour_expr
from bluebird_pipeline.gold.aggregator_bluebird_day_chance import BluebirdDayParams

NOON = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)


@pytest.mark.parametrize(
    ("row", "sunny"),
    [
        ({"cloud_cover_pct": 10.0, "shortwave_wm2": 350.0}, True),
        ({"cloud_cover_pct": 60.0, "shortwave_wm2": 350.0}, False),  # too cloudy
        ({"cloud_cover_pct": 10.0, "shortwave_wm2": 150.0}, False),  # hazy: < 0.6 x ~390
        ({"cloud_cover_pct": None, "shortwave_wm2": 350.0}, None),  # missing value
    ],
)
def test_sunny_hour_rule(row: dict[str, float | None], sunny: bool | None) -> None:
    frame = pl.DataFrame(
        [{"time_utc": NOON, **row}], schema_overrides={"cloud_cover_pct": pl.Float64}
    )
    expr = sunny_hour_expr(30.0, 0.6, clear_sky_expr("time_utc", 42.9, 0.1))
    assert frame.select(expr).item() is sunny


def test_low_sun_hours_only_need_a_clear_sky() -> None:
    dawn = datetime(2026, 1, 15, 8, 0, tzinfo=UTC)  # sun barely up in the Pyrenees
    frame = pl.DataFrame([{"time_utc": dawn, "cloud_cover_pct": 0.0, "shortwave_wm2": 5.0}])
    expr = sunny_hour_expr(30.0, 0.6, clear_sky_expr("time_utc", 42.9, 0.1))
    assert frame.select(expr).item() is True


def test_params_check_the_sunny_hours() -> None:
    with pytest.raises(ValidationError, match="min_sunny_hours exceeds"):
        BluebirdDayParams(min_sunny_hours=9)
    with pytest.raises(ValidationError, match="ski_end must be after"):
        BluebirdDayParams(ski_start="17:00", ski_end="09:00")


def test_bluebird_day_needs_fresh_snow_and_sun(ctx: RunContext) -> None:
    # Run date 2026-12-14 (Europe/Paris): ski hours end 09:00-16:00 UTC, fresh snow
    # counted over the 36 h before 08:00 UTC. Members 0-5 get 1 cm/h all of Dec 13
    # (24 cm); members 0-2 then have a clear sky, 3-5 an overcast one; 6-9 no snow.
    start = datetime(2026, 12, 12, 12, tzinfo=UTC)

    def values(station: str, member: int, when: datetime) -> dict[str, float]:
        snowing = member < 6 and when.date().isoformat() == "2026-12-13"
        clear = member < 3 or member >= 6
        return {
            "snowfall_cm": 1.0 if snowing else 0.0,
            "cloud_cover_pct": 0.0 if clear else 90.0,
            "shortwave_wm2": 1000.0 if clear else 50.0,
        }

    frame = ensemble_frame(
        stations=["alpha", "beta"], bands=["mid"], members=10, start=start, hours=80, values=values
    )
    ctx._silver_cache["ensemble_hourly"] = frame
    kpi = ctx.config.kpi("bluebird_day_chance")
    results = AGGREGATORS.get(kpi.aggregator)(kpi).aggregate(ctx)
    assert {r.period_id for r in results} == {"day"}
    today = {r.station_id: r for r in results if r.forecast_date.isoformat() == "2026-12-14"}
    assert {s: r.probability for s, r in today.items()} == {"alpha": 0.3, "beta": 0.3}
    assert today["alpha"].members == 10
    assert today["alpha"].drivers["sunny_hours_p50"] == 8
    # Tomorrow's 36 h only catch the last 4 hours of the snowfall: no bluebird day.
    tomorrow = [r for r in results if r.forecast_date.isoformat() == "2026-12-15"]
    assert tomorrow and all(r.probability == 0.0 for r in tomorrow)
