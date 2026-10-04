"""Gold files per KPI and the fallback on values of earlier runs."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import polars as pl

from bluebird_pipeline.context import PeriodInstance, RunContext
from bluebird_pipeline.gold.base import KpiResult, read_gold, results_to_frame
from bluebird_pipeline.runner import RunReport, run_gold_kpi
from bluebird_pipeline.storage import gold_key


def _instance(ctx: RunContext, key: str) -> PeriodInstance:
    massif = ctx.massifs()[0]
    instances = ctx.period_instances(massif, visible_only=False)
    return next(i for i in instances if i.key == key)


def _result(instance: PeriodInstance, station_id: str, probability: float) -> KpiResult:
    return KpiResult(
        kpi_id="snowfall_chance",
        station_id=station_id,
        massif_id="pyrenees",
        forecast_date=instance.ski_day,
        period_id=instance.period_id,
        period_start=instance.start,
        period_end=instance.end,
        probability=probability,
        confidence="high",
        window_start=instance.start,
        window_end=instance.end,
        members=91,
        drivers={},
        aggregator="snowfall_chance",
        aggregator_version="2",
    )


def _write(ctx: RunContext, day: date, results: list[KpiResult], when: datetime) -> None:
    run_id = when.strftime("%Y%m%dT%H%M%SZ")
    ctx.storage.write_parquet(
        gold_key(day, "snowfall_chance"), results_to_frame(results, run_id, when)
    )


def test_read_gold_keeps_the_latest_run_of_each_period(ctx: RunContext) -> None:
    evening = _instance(ctx, "evening@2026-12-14")
    morning = _instance(ctx, "morning@2026-12-15")
    older = ctx.generated_at - timedelta(hours=6)
    # The day before's file still holds periods of the 14th and 15th.
    _write(
        ctx,
        ctx.run_date - timedelta(days=1),
        [_result(evening, "alpha", 0.1), _result(morning, "alpha", 0.3)],
        older,
    )
    _write(ctx, ctx.run_date, [_result(evening, "alpha", 0.9)], ctx.generated_at)

    gold = read_gold(ctx, ["snowfall_chance"])
    by_period = dict(gold.select("period_id", "probability").iter_rows())
    assert by_period == {"evening": 0.9, "morning": 0.3}


def test_read_gold_drops_periods_over_and_files_without_periods(ctx: RunContext) -> None:
    morning = _instance(ctx, "morning@2026-12-14")
    midday = _instance(ctx, "midday@2026-12-14")
    _write(
        ctx,
        ctx.run_date,
        [_result(morning, "alpha", 0.5), _result(midday, "alpha", 0.5)],
        ctx.generated_at,
    )
    ctx.storage.write_parquet(
        f"gold/kpis/date={ctx.run_date}/kpis.parquet", pl.DataFrame({"kpi_id": ["x"]})
    )
    noon = RunContext.create(  # the 12:00 refresh: the morning is over
        ctx.config, ctx.storage, now=datetime(2026, 12, 14, 11, 7, tzinfo=UTC)
    )
    assert read_gold(noon, ["snowfall_chance"])["period_id"].to_list() == ["midday"]


def test_a_kpi_that_cannot_run_keeps_its_earlier_values_as_stale(ctx: RunContext) -> None:
    evening = _instance(ctx, "evening@2026-12-14")
    earlier = ctx.generated_at - timedelta(hours=6)
    _write(ctx, ctx.run_date, [_result(evening, "alpha", 0.4)], earlier)

    report = RunReport()
    run_gold_kpi(ctx, ctx.config.kpi("snowfall_chance"), report)  # no silver data at all

    assert any("no silver data" in e for e in report.errors)
    [step] = report.steps
    assert step.state == "stale"
    kept = ctx.storage.read_parquet(gold_key(ctx.run_date, "snowfall_chance"))
    assert kept["probability"].to_list() == [0.4]
    assert kept["generated_at"].to_list() == [earlier.replace(tzinfo=UTC)]


def test_a_kpi_without_values_nor_history_is_down(ctx: RunContext) -> None:
    report = RunReport()
    run_gold_kpi(ctx, ctx.config.kpi("snowfall_chance"), report)
    assert report.steps[0].state == "down"
    assert not ctx.storage.exists(gold_key(ctx.run_date, "snowfall_chance"))
