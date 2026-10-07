"""Live KPIs built from the fetched ensemble: snow, snow quality, sky, comfort, access, safety.

Each test builds a synthetic ensemble where the first members meet the KPI's
condition and the others do not, so the probability is a known share. Run
date 2026-12-14 (Europe/Paris, UTC+1): the frame covers 12-16 December.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

import pytest
from _factories import ensemble_frame

from bluebird_pipeline.context import RunContext
from bluebird_pipeline.gold import AGGREGATORS
from bluebird_pipeline.gold._conditions import sunset_utc
from bluebird_pipeline.gold.base import KpiResult

PARIS = ZoneInfo("Europe/Paris")
START = datetime(2026, 12, 12, 0, tzinfo=UTC)
HOURS = 120  # to 17 December: tomorrow's 36-hour snow window ends on the 16th, 17:00 UTC

Values = Callable[[int, datetime], dict[str, float]]

CALM = {
    "relative_humidity_pct": 60.0,
    "cloud_cover_pct": 0.0,
    "cloud_cover_low_pct": 0.0,
    "shortwave_wm2": 1000.0,
}


def run(ctx: RunContext, kpi_id: str, values: Values) -> list[KpiResult]:
    frame = ensemble_frame(
        stations=["alpha", "beta"],
        bands=["mid", "summit"],
        members=10,
        start=START,
        hours=HOURS,
        values=lambda station, member, when: {**CALM, **values(member, when)},
    )
    ctx._silver_cache["ensemble_hourly"] = frame
    kpi = ctx.config.kpi(kpi_id)
    return AGGREGATORS.get(kpi.aggregator)(kpi).aggregate(ctx)


def probabilities(results: list[KpiResult]) -> dict[str, set[float]]:
    """Probabilities per period key, over both stations."""
    out: dict[str, set[float]] = {}
    for r in results:
        out.setdefault(f"{r.period_id}@{r.forecast_date.isoformat()}", set()).add(r.probability)
    return out


def local_hour(when: datetime) -> int:
    """Local hour (Paris) at the start of the hour ending at ``when``."""
    return (when.astimezone(PARIS).hour - 1) % 24


def test_wet_bulb_wind_chill_and_sunset_match_reference_values() -> None:
    import polars as pl

    from bluebird_pipeline.gold._conditions import wet_bulb_expr, wind_chill_expr

    frame = pl.DataFrame(
        {"temperature_c": [20.0, -10.0, 5.0], "relative_humidity_pct": [50.0, 80.0, 50.0]}
    ).with_columns(wind_speed_kmh=pl.Series([10.0, 30.0, 2.0]))
    wet = frame.select(wet_bulb_expr()).to_series().to_list()
    assert wet[0] == pytest.approx(13.7, abs=0.1)  # Stull (2011) worked example
    chill = frame.select(wind_chill_expr()).to_series().to_list()
    assert chill[1] == pytest.approx(-19.5, abs=0.3)  # wind chill table: -10 °C, 30 km/h
    assert chill[2] == 5.0  # no wind chill without wind
    sunset = sunset_utc(date(2027, 1, 15), 42.9, 0.1).astimezone(PARIS)
    assert (sunset.hour, sunset.minute // 10) == (17, 4)  # 17:43 in Lourdes


#: Day-grain version (period, probability) of the KPIs that also have time slots:
#: computed over the whole ski day, with the same synthetic scenarios.
DAY_GRAIN = {
    "snowmaking_chance": ("overnight", 0.5),
    "spring_snow_chance": ("day", 0.3),
    "hard_snow_chance": ("day", 0.6),
    "heavy_snow_chance": ("day", 0.2),
    "easy_conditions_chance": ("day", 0.7),
    "starry_night_chance": ("sunset", 0.5),
    "sunny_slot_chance": ("day", 0.4),
    "wind_chill_chance": ("day", 0.3),
    "lift_wind_chance": ("day", 0.2),
}


@pytest.mark.parametrize(
    ("kpi_id", "values", "expected"),
    [
        # Snow: 1 cm/h for members 0-3 -> 36 cm in 36 h.
        (
            "powder_alert_chance",
            lambda m, w: {"snowfall_cm": 1.0 if m < 4 else 0.0},
            {"day@2026-12-14": {0.4}, "day@2026-12-15": {0.4}},
        ),
        # Cold, dry nights for members 0-4 (wet-bulb about -10 °C).
        (
            "snowmaking_chance",
            lambda m, w: {"temperature_c": -8.0 if m < 5 else 2.0},
            {"night@2026-12-14": {0.5}, "night@2026-12-15": {0.5}},
        ),
        # Members 0-2 freeze at night and soften from 10:00.
        (
            "spring_snow_chance",
            lambda m, w: {
                "temperature_c": (5.0 if local_hour(w) >= 10 else -4.0) if m < 3 else -5.0
            },
            {
                **{f"{p}@2026-12-14": {0.3} for p in ("morning", "midday", "afternoon")},
                **{f"{p}@2026-12-15": {0.3} for p in ("morning", "midday", "afternoon")},
            },
        ),
        # Members 0-5 melt in the afternoon (13:00-17:00) and freeze the rest of the time.
        (
            "hard_snow_chance",
            lambda m, w: {"temperature_c": 4.0 if m < 6 and 12 <= local_hour(w) <= 16 else -5.0},
            {"morning@2026-12-14": {0.6}, "morning@2026-12-15": {0.6}},
        ),
        # Members 0-1 are warm all day.
        (
            "heavy_snow_chance",
            lambda m, w: {"temperature_c": 6.0 if m < 2 else -2.0},
            {
                **{f"{p}@2026-12-14": {0.2} for p in ("midday", "afternoon")},
                **{f"{p}@2026-12-15": {0.2} for p in ("midday", "afternoon")},
            },
        ),
        # Members 7-9 have a strong wind.
        (
            "easy_conditions_chance",
            lambda m, w: {"wind_speed_kmh": 40.0 if m >= 7 else 10.0},
            {
                **{f"{p}@2026-12-14": {0.7} for p in ("morning", "midday", "afternoon")},
                **{f"{p}@2026-12-15": {0.7} for p in ("morning", "midday", "afternoon")},
            },
        ),
        # Sky: members 0-7 clear.
        (
            "sunset_chance",
            lambda m, w: {"cloud_cover_pct": 10.0 if m < 8 else 90.0},
            {"sunset@2026-12-14": {0.8}, "sunset@2026-12-15": {0.8}},
        ),
        (
            "starry_night_chance",
            lambda m, w: {"cloud_cover_pct": 5.0 if m < 5 else 80.0},
            {"evening@2026-12-14": {0.5}, "evening@2026-12-15": {0.5}},
        ),
        # Members 0-3 sunny; the morning only counts its daylight hours.
        (
            "sunny_slot_chance",
            lambda m, w: {"cloud_cover_pct": 0.0 if m < 4 else 80.0},
            {
                **{f"{p}@2026-12-14": {0.4} for p in ("morning", "midday", "afternoon")},
                **{f"{p}@2026-12-15": {0.4} for p in ("morning", "midday", "afternoon")},
            },
        ),
        # Comfort: -15 °C in a 40 km/h wind feels like about -26 °C.
        (
            "wind_chill_chance",
            lambda m, w: (
                {"temperature_c": -15.0, "wind_speed_kmh": 40.0}
                if m < 3
                else {"temperature_c": -5.0}
            ),
            {
                **{f"{p}@2026-12-14": {0.3} for p in ("morning", "midday", "afternoon")},
                **{f"{p}@2026-12-15": {0.3} for p in ("morning", "midday", "afternoon")},
            },
        ),
        (
            "mild_day_chance",
            lambda m, w: {"temperature_c": 8.0 if m < 5 else 0.0},
            {"day@2026-12-14": {0.5}, "day@2026-12-15": {0.5}},
        ),
        # Access: -3 °C at 2000 m is about 0 °C on a road at 1400-1500 m.
        (
            "chains_chance",
            lambda m, w: {"snowfall_cm": 0.5, "temperature_c": -3.0 if m < 6 else 2.0},
            {"day@2026-12-14": {0.6}, "day@2026-12-15": {0.6}},
        ),
        (
            "lift_wind_chance",
            lambda m, w: {"wind_speed_kmh": 60.0 if m < 2 else 20.0},
            {
                **{f"{p}@2026-12-14": {0.2} for p in ("morning", "midday", "afternoon")},
                **{f"{p}@2026-12-15": {0.2} for p in ("morning", "midday", "afternoon")},
            },
        ),
        # Safety: members 0-6 get 24 cm in 48 h, only 0-4 with a strong wind.
        (
            "wind_slab_chance",
            lambda m, w: {
                "snowfall_cm": 0.5 if m < 7 else 0.0,
                "wind_speed_kmh": 40.0 if m < 5 else 10.0,
            },
            {"day@2026-12-14": {0.5}, "day@2026-12-15": {0.5}},
        ),
    ],
)
def test_probability_is_the_share_of_scenarios_meeting_the_condition(
    ctx: RunContext, kpi_id: str, values: Values, expected: dict[str, set[float]]
) -> None:
    if kpi_id in DAY_GRAIN:
        period, probability = DAY_GRAIN[kpi_id]
        expected = expected | {f"{period}@2026-12-1{d}": {probability} for d in (4, 5)}
    results = run(ctx, kpi_id, values)
    assert probabilities(results) == expected
    assert all(r.members == 10 for r in results)


def test_sunset_reports_its_time_and_window(ctx: RunContext) -> None:
    results = run(ctx, "sunset_chance", lambda m, w: {})
    today = next(r for r in results if r.forecast_date.isoformat() == "2026-12-14")
    assert today.drivers["sunset_time"] == "17:26"  # mid-December, Paris time
    # The hour before, the hour of the sunset and the hour after.
    assert (today.window_start.hour, today.window_end.hour) == (16, 19)


def test_chains_report_the_road_elevation(ctx: RunContext) -> None:
    results = run(ctx, "chains_chance", lambda m, w: {"snowfall_cm": 0.5, "temperature_c": -3.0})
    bases = {r.station_id: r.drivers["base_m"] for r in results}
    assert bases == {"alpha": 1500, "beta": 1400}
    assert all(r.probability == 1.0 for r in results)
