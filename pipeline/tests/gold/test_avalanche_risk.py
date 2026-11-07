"""KPI ``avalanche_risk``: the danger level of the Météo-France bulletin, relayed as is."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import polars as pl
import pytest

from bluebird_pipeline.config import Config, Kpi, KpiDisplay
from bluebird_pipeline.context import RunContext
from bluebird_pipeline.demo import demo_bulletins
from bluebird_pipeline.diamond._status import kpi_status
from bluebird_pipeline.gold import AGGREGATORS
from bluebird_pipeline.gold.aggregator_avalanche_risk import level_at
from bluebird_pipeline.gold.base import KpiResult, read_gold
from bluebird_pipeline.runner import RunReport, run_gold_kpi
from bluebird_pipeline.silver._avalanche import AVALANCHE_DATASET, AVALANCHE_SCHEMA
from bluebird_pipeline.storage import LocalStorage

NOW = datetime(2027, 1, 15, 5, 7, tzinfo=UTC)  # the 06:00 refresh (Paris)
TODAY = date(2027, 1, 15)


def bulletin(
    number: int,
    low: int,
    high: int,
    limit: int | None,
    issued: datetime,
    *,
    valid: date = TODAY,
    trend: bool = False,
) -> dict:
    return {
        "massif_number": number,
        "massif_name": f"Massif {number}",
        "valid_date": valid,
        "level_low": low,
        "level_high": high,
        "altitude_limit_m": limit,
        "trend": trend,
        "issued_at": issued,
    }


def run(repo_config: Config, tmp_path, rows: list[dict]) -> dict[str, KpiResult]:
    return {
        (r.station_id): r for r in run_all(repo_config, tmp_path, rows) if r.forecast_date == TODAY
    }


def run_all(repo_config: Config, tmp_path, rows: list[dict]) -> list[KpiResult]:
    ctx = RunContext.create(repo_config, LocalStorage(tmp_path), now=NOW)
    ctx._silver_cache[AVALANCHE_DATASET] = pl.DataFrame(rows, schema=AVALANCHE_SCHEMA)
    kpi = ctx.config.kpi("avalanche_risk")
    return AGGREGATORS.get(kpi.aggregator)(kpi).aggregate(ctx)


def test_level_depends_on_the_summit_and_the_altitude_limit() -> None:
    assert level_at(2415, 3, 4, 2450) == 3  # summit below the limit
    assert level_at(2500, 3, 4, 2450) == 4
    assert level_at(2450, 3, 4, 2450) == 4  # at the limit: above
    assert level_at(1800, 2, 2, None) == 2  # no limit: the same level everywhere


def test_each_station_gets_the_level_of_its_massif(repo_config: Config, tmp_path) -> None:
    fresh = datetime(2027, 1, 14, 15, 0, tzinfo=UTC)  # yesterday 16:00 local
    old = datetime(2027, 1, 13, 15, 0, tzinfo=UTC)
    results = run(
        repo_config,
        tmp_path,
        [
            bulletin(66, 3, 4, 2450, fresh),  # Haute-Bigorre
            bulletin(65, 2, 2, None, old),  # Aspe Ossau, issued 38 h ago
        ],
    )
    # Only the stations of the two massifs, today only (no bulletin for tomorrow).
    assert set(results) == {
        "grand-tourmalet",
        "luz-ardiden",
        "cauterets",
        "piau-engaly",
        "gourette",
    }
    assert all(r.period_id == "day" and r.forecast_date == TODAY for r in results.values())

    cauterets, luz = results["cauterets"], results["luz-ardiden"]  # summits 2415 m, 2500 m
    assert (cauterets.drivers["level"], luz.drivers["level"]) == (3, 4)
    assert (cauterets.probability, luz.probability) == (0.5, 0.75)
    assert cauterets.members == 0
    assert cauterets.confidence == "high"
    assert results["gourette"].confidence == "medium"  # older than fresh_hours (24)
    assert results["gourette"].drivers["massif"] == "Massif 65"


def test_the_latest_bulletin_wins(repo_config: Config, tmp_path) -> None:
    results = run(
        repo_config,
        tmp_path,
        [
            bulletin(66, 3, 3, None, datetime(2027, 1, 14, 15, 0, tzinfo=UTC)),
            bulletin(66, 4, 4, None, datetime(2027, 1, 14, 18, 0, tzinfo=UTC)),  # update
        ],
    )
    assert results["cauterets"].drivers["level"] == 4


def test_tomorrow_shows_the_trend_until_its_bulletin(repo_config: Config, tmp_path) -> None:
    tomorrow = TODAY + timedelta(days=1)
    issued = datetime(2027, 1, 14, 15, 0, tzinfo=UTC)
    trend = bulletin(66, 4, 4, None, issued, valid=tomorrow, trend=True)
    by_day = {
        r.forecast_date: r
        for r in run_all(repo_config, tmp_path, [trend])
        if r.station_id == "cauterets"
    }
    assert set(by_day) == {tomorrow}  # nothing for today without its bulletin
    assert by_day[tomorrow].drivers["level"] == 4
    assert by_day[tomorrow].confidence == "medium"  # a trend, even a fresh one

    # The afternoon bulletin wins over the trend, even issued earlier in the list.
    real = bulletin(66, 3, 3, None, issued - timedelta(hours=1), valid=tomorrow)
    by_day = {
        r.forecast_date: r
        for r in run_all(repo_config, tmp_path, [trend, real])
        if r.station_id == "cauterets"
    }
    assert by_day[tomorrow].drivers["level"] == 3
    assert by_day[tomorrow].confidence == "high"


def test_no_bulletin_out_of_season_is_reported_ok(repo_config: Config, tmp_path) -> None:
    ctx = RunContext.create(repo_config, LocalStorage(tmp_path), now=NOW)
    ctx._silver_cache[AVALANCHE_DATASET] = pl.DataFrame(schema=AVALANCHE_SCHEMA)
    report = RunReport()
    run_gold_kpi(ctx, ctx.config.kpi("avalanche_risk"), report)
    (step,) = report.steps
    assert (step.state, step.ok, step.expected) == ("ok", 0, 0)
    assert not report.errors

    # A missing silver table (the source failed) is still a failure.
    ctx._silver_cache[AVALANCHE_DATASET] = None
    report = RunReport()
    run_gold_kpi(ctx, ctx.config.kpi("avalanche_risk"), report)
    assert report.steps[0].state == "down"


def test_demo_bulletins_of_tomorrow_wait_for_the_afternoon(repo_config: Config, tmp_path) -> None:
    morning = demo_bulletins(RunContext.create(repo_config, LocalStorage(tmp_path), now=NOW))
    bulletins = morning.filter(~pl.col("trend"))
    assert set(bulletins["valid_date"]) == {TODAY}
    assert set(morning.filter(pl.col("trend"))["valid_date"]) == {TODAY + timedelta(days=1)}
    evening = RunContext.create(
        repo_config, LocalStorage(tmp_path), now=datetime(2027, 1, 15, 17, 7, tzinfo=UTC)
    )
    assert len(set(demo_bulletins(evening).filter(~pl.col("trend"))["valid_date"])) == 2


@pytest.mark.parametrize(
    ("steps", "message"),
    [
        ([], "`steps` by increasing value"),
        ([2, 1], "`steps` by increasing value"),
        ([1, 1], "`steps` by increasing value"),
    ],
)
def test_a_scale_display_needs_increasing_steps(steps: list[int], message: str) -> None:
    label = {"fr": "x", "en": "x", "es": "x"}
    with pytest.raises(ValueError, match=message):
        KpiDisplay.model_validate(
            {
                "kind": "scale",
                "driver": "level",
                "steps": [{"value": v, "tone": "danger-1", "label": label} for v in steps],
            }
        )


def test_the_status_page_shows_no_bulletin_as_ok(repo_config: Config, tmp_path) -> None:
    ctx = RunContext.create(repo_config, LocalStorage(tmp_path), now=NOW)
    statuses = {
        k.id: k for k in kpi_status(ctx, read_gold(ctx, ["avalanche_risk", "snowfall_chance"]))
    }
    assert statuses["avalanche_risk"].state == "ok"
    assert statuses["snowfall_chance"].state == "down"  # a weather KPI without data is down


def test_an_official_link_needs_a_certified_kpi(repo_config: Config) -> None:
    data = repo_config.kpi("avalanche_risk").model_dump(mode="json")
    assert data["official_link"]["url"].startswith("https://meteofrance.com/")
    with pytest.raises(ValueError, match="`official_link` needs `certified: true`"):
        Kpi.model_validate({**data, "certified": False})
