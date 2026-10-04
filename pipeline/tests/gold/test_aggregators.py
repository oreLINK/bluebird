"""KPI models on synthetic silver data with known answers.

Ski day 2026-12-14, Europe/Paris = UTC+1, run at 05:30 local: every period of
the 14th and 15th is still to come. Station ``alpha`` grooms until 02:00 and
opens at 09:00; ``beta`` grooms until 22:00 the previous evening.
"""

from __future__ import annotations

from datetime import UTC, datetime

import polars as pl
import pytest
from _factories import ensemble_frame

from bluebird_pipeline.context import RunContext
from bluebird_pipeline.gold import AGGREGATORS, KpiResult, confidence_level
from bluebird_pipeline.storage import silver_key

START = datetime(2026, 12, 12, 0, tzinfo=UTC)
HOURS = 72  # 12th 00:00 UTC -> 14th 23:00 UTC


def _store(ctx: RunContext, values, members: int = 10) -> None:
    frame = ensemble_frame(
        stations=["alpha", "beta"],
        bands=["mid", "summit"],
        members=members,
        start=START,
        hours=HOURS,
        values=values,
    )
    ctx.storage.write_parquet(silver_key("ensemble_hourly", ctx.run_date, ctx.run_id), frame)
    ctx.invalidate_silver()


def _all(ctx: RunContext, kpi_id: str) -> list[KpiResult]:
    kpi = ctx.config.kpi(kpi_id)
    return AGGREGATORS.get(kpi.aggregator)(kpi).aggregate(ctx)


def _run(ctx: RunContext, kpi_id: str, period: str = "day@2026-12-14") -> dict[str, KpiResult]:
    """Results of one period instance (``period_id@ski_day``), by station."""
    return {
        r.station_id: r
        for r in _all(ctx, kpi_id)
        if f"{r.period_id}@{r.forecast_date.isoformat()}" == period
    }


def test_snowfall_chance_counts_members_above_threshold(ctx: RunContext) -> None:
    # Window (08:00, 17:00] local = timestamps 08:00..16:00 UTC: 9 hours.
    # Members 0-6 get 0.5 cm/h all day on the 14th, others nothing.
    def values(station: str, member: int, when: datetime) -> dict:
        return {"snowfall_cm": 0.5 if member < 7 and when.day == 14 else 0.0}

    _store(ctx, values)
    alpha = _run(ctx, "snowfall_chance")["alpha"]
    assert alpha.probability == pytest.approx(0.7)
    assert alpha.members == 10
    assert alpha.drivers["snow_cm_p50"] == pytest.approx(4.5)  # 9 hours x 0.5 cm
    assert alpha.window_start.isoformat() == "2026-12-14T08:00:00+01:00"
    assert alpha.confidence == "medium"  # agreement |2*0.7-1| = 0.4
    assert alpha.period_end.isoformat() == "2026-12-14T18:00:00+01:00"


def test_time_slots_use_their_own_hours(ctx: RunContext) -> None:
    # 1 cm/h only for the hours ending 07:00-12:00 local on the 14th (06-11 UTC).
    def values(station: str, member: int, when: datetime) -> dict:
        morning = when.day == 14 and 6 <= when.hour <= 11
        return {"snowfall_cm": 1.0 if morning else 0.0}

    _store(ctx, values)
    assert _run(ctx, "snowfall_chance", "morning@2026-12-14")["alpha"].probability == 1.0
    midday = _run(ctx, "snowfall_chance", "midday@2026-12-14")["alpha"]
    assert midday.probability == 0.0
    assert midday.window_start.isoformat() == "2026-12-14T12:00:00+01:00"
    assert midday.window_end.isoformat() == "2026-12-14T14:00:00+01:00"


def test_periods_without_data_or_already_over_are_skipped(ctx: RunContext) -> None:
    _store(ctx, lambda station, member, when: {"snowfall_cm": 0.2})
    keys = {f"{r.period_id}@{r.forecast_date}" for r in _all(ctx, "snowfall_chance")}
    # Silver stops at 14th 23:00 UTC: the evening of the 14th ends at midnight
    # local (23:00 UTC) and is complete; nothing of the 15th after that is.
    assert "evening@2026-12-14" in keys
    assert "night@2026-12-14" not in keys
    assert not any(k.endswith("2026-12-15") for k in keys)

    later = RunContext.create(
        ctx.config, ctx.storage, now=datetime(2026, 12, 14, 11, 7, tzinfo=UTC)
    )  # the 12:00 refresh
    later.storage.write_parquet(
        silver_key("ensemble_hourly", later.run_date, later.run_id),
        ctx.silver("ensemble_hourly"),
    )
    keys = {f"{r.period_id}@{r.forecast_date}" for r in _all(later, "snowfall_chance")}
    assert "morning@2026-12-14" not in keys
    assert {"day@2026-12-14", "midday@2026-12-14"} <= keys


def test_onpiste_window_starts_previous_evening_when_grooming_ends_late(ctx: RunContext) -> None:
    # 1.5 cm/h for the hours ending 23:00-02:00 local (22:00-01:00 UTC): 6 cm.
    # beta (window from 22:00 local the day before) gets it all, alpha
    # (window from 02:00 local) gets none of it.
    night = {
        datetime(2026, 12, 13, 22, tzinfo=UTC),
        datetime(2026, 12, 13, 23, tzinfo=UTC),
        datetime(2026, 12, 14, 0, tzinfo=UTC),
        datetime(2026, 12, 14, 1, tzinfo=UTC),
    }

    def values(station: str, member: int, when: datetime) -> dict:
        return {"snowfall_cm": 1.5 if when in night else 0.0}

    _store(ctx, values)
    results = _run(ctx, "onpiste_powder_chance", "morning@2026-12-14")
    assert results["alpha"].probability == 0.0
    assert results["beta"].probability == 1.0
    assert results["beta"].window_start.isoformat() == "2026-12-13T22:00:00+01:00"
    assert results["beta"].window_end.isoformat() == "2026-12-14T09:00:00+01:00"  # opening
    assert results["beta"].drivers["window_hours"] == 11

    # Later slots look at the snow fallen since grooming until they start.
    afternoon = _run(ctx, "onpiste_powder_chance", "afternoon@2026-12-14")["alpha"]
    assert afternoon.window_end.isoformat() == "2026-12-14T14:00:00+01:00"


def test_offpiste_powder_is_penalised_by_wind_and_thaw(ctx: RunContext) -> None:
    # Everyone gets 1 cm/h for 20 h before opening (20 cm >= 15 cm threshold).
    # alpha: calm and cold -> 1.0. beta: 60+ km/h wind -> wind floor 0.3, and
    # members 0-4 also thaw (> 0.5 °C) -> 0.3 x 0.3.
    def values(station: str, member: int, when: datetime) -> dict:
        hours_before_opening = (datetime(2026, 12, 14, 8, tzinfo=UTC) - when).total_seconds() / 3600
        snowing = 0 <= hours_before_opening < 20
        windy = station == "beta"
        warm = station == "beta" and member < 5
        return {
            "snowfall_cm": 1.0 if snowing else 0.0,
            "wind_speed_kmh": 70.0 if windy else 10.0,
            "temperature_c": 2.0 if warm else -6.0,
        }

    _store(ctx, values)
    results = _run(ctx, "offpiste_powder_chance", "morning@2026-12-14")
    assert results["alpha"].probability == pytest.approx(1.0)
    assert results["alpha"].drivers["new_snow_cm_p50"] == 20
    assert results["beta"].probability == pytest.approx((5 * 0.3 * 0.3 + 5 * 0.3) / 10)
    assert results["beta"].drivers["max_wind_kmh_p50"] == 70


def test_members_with_missing_hours_are_ignored(ctx: RunContext) -> None:
    def values(station: str, member: int, when: datetime) -> dict:
        missing = member == 0 and when == datetime(2026, 12, 14, 11, tzinfo=UTC)
        return {"snowfall_cm": None if missing else 0.2}

    _store(ctx, values)
    assert _run(ctx, "snowfall_chance")["alpha"].members == 9


def test_stations_without_data_are_skipped(ctx: RunContext) -> None:
    _store(ctx, lambda station, member, when: {})
    alpha_only = ctx.silver("ensemble_hourly").filter(pl.col("station_id") == "alpha")
    ctx.storage.write_parquet(silver_key("ensemble_hourly", ctx.run_date, ctx.run_id), alpha_only)
    ctx.invalidate_silver()
    assert set(_run(ctx, "snowfall_chance")) == {"alpha"}


@pytest.mark.parametrize(
    ("probability", "members", "expected"),
    [
        (0.95, 91, "high"),
        (0.05, 91, "high"),
        (0.7, 91, "medium"),
        (0.5, 91, "low"),
        (1.0, 5, "low"),
    ],
)
def test_confidence_level(probability: float, members: int, expected: str) -> None:
    assert confidence_level(probability, members) == expected
