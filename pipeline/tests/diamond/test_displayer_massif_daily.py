from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from bluebird_pipeline.context import PeriodInstance, RunContext
from bluebird_pipeline.diamond import DISPLAYERS
from bluebird_pipeline.diamond._status import build_manifest, build_status, finalize_refresh
from bluebird_pipeline.diamond.models import DiamondMassifDaily, DiamondStatus
from bluebird_pipeline.gold.base import KpiResult, results_to_frame
from bluebird_pipeline.report import StepReport
from bluebird_pipeline.storage import gold_key, status_key


def _instance(ctx: RunContext, key: str) -> PeriodInstance:
    instances = ctx.period_instances(ctx.massifs()[0], visible_only=False)
    return next(i for i in instances if i.key == key)


def _result(
    ctx: RunContext,
    kpi_id: str,
    station_id: str,
    probability: float,
    period: str = "day@2026-12-14",
) -> KpiResult:
    instance = _instance(ctx, period)
    return KpiResult(
        kpi_id=kpi_id,
        station_id=station_id,
        massif_id="pyrenees",
        forecast_date=instance.ski_day,
        period_id=instance.period_id,
        period_start=instance.start,
        period_end=instance.end,
        probability=probability,
        confidence="high",
        window_start=datetime(2026, 12, 14, 7, tzinfo=UTC),
        window_end=datetime(2026, 12, 14, 16, tzinfo=UTC),
        members=91,
        drivers={"snow_cm_p50": 3.5},
        aggregator=kpi_id,
        aggregator_version="2",
    )


def _write_gold(ctx: RunContext, results: list[KpiResult], when: datetime | None = None) -> None:
    when = when or ctx.generated_at
    for kpi_id in {r.kpi_id for r in results}:
        rows = [r for r in results if r.kpi_id == kpi_id]
        frame = results_to_frame(rows, when.strftime("%Y%m%dT%H%M%SZ"), when)
        ctx.storage.write_parquet(gold_key(ctx.run_date, kpi_id), frame)


def _display(ctx: RunContext) -> None:
    for artifact in DISPLAYERS.get("massif_daily")().display(ctx):
        ctx.storage.write_json(artifact.key, artifact.payload.model_dump(mode="json"))


def test_rankings_are_sorted_per_period_and_times_are_local(ctx: RunContext) -> None:
    _write_gold(
        ctx,
        [
            _result(ctx, "snowfall_chance", "alpha", 0.2),
            _result(ctx, "snowfall_chance", "beta", 0.8),
            _result(ctx, "snowfall_chance", "alpha", 0.6, "evening@2026-12-14"),
            _result(ctx, "onpiste_powder_chance", "alpha", 0.5, "morning@2026-12-14"),
        ],
    )
    artifacts = DISPLAYERS.get("massif_daily")().display(ctx)
    assert [a.key for a in artifacts] == [
        "diamond/pyrenees/latest.json",
        "diamond/pyrenees/2026-12-14.json",
    ]

    payload = artifacts[0].payload
    assert isinstance(payload, DiamondMassifDaily)
    assert payload.schema_version == 2
    snowfall = payload.kpis["snowfall_chance"].periods
    assert [p.key for p in snowfall] == ["day@2026-12-14", "evening@2026-12-14"]
    ranking = snowfall[0].ranking
    assert [r.station_id for r in ranking] == ["beta", "alpha"]
    assert ranking[0].window_start.isoformat() == "2026-12-14T08:00:00+01:00"
    assert snowfall[1].start.isoformat() == "2026-12-14T18:00:00+01:00"
    assert snowfall[1].generated_at == ctx.generated_at
    assert "offpiste_powder_chance" not in payload.kpis  # no gold rows for it
    assert set(payload.stations) == {"alpha", "beta"}
    assert payload.stations["alpha"].elevation.mid == 2000
    assert {s.id for s in payload.sources} == {"open_meteo_ensemble", "open_meteo_forecast"}

    # Round-trips through JSON exactly as the frontend will read it.
    DiamondMassifDaily.model_validate_json(payload.model_dump_json())


def test_missing_gold_is_an_error(ctx: RunContext) -> None:
    with pytest.raises(FileNotFoundError, match="run the gold layer first"):
        DISPLAYERS.get("massif_daily")().display(ctx)


def test_status_reports_every_unit(ctx: RunContext) -> None:
    earlier = ctx.generated_at - timedelta(hours=6)
    fresh = [
        _result(ctx, "snowfall_chance", "alpha", 0.2),
        _result(ctx, "snowfall_chance", "beta", 0.4),
        _result(ctx, "snowfall_chance", "alpha", 0.3, "evening@2026-12-14"),  # beta missing
    ]
    _write_gold(ctx, fresh)
    _write_gold(
        ctx, [_result(ctx, "onpiste_powder_chance", "alpha", 0.5, "morning@2026-12-14")], earlier
    )
    _display(ctx)
    steps = [
        StepReport(layer="bronze", id="open_meteo_ensemble", state="ok"),
        StepReport(layer="silver", id="open_meteo_ensemble", state="ok", ok=2, expected=2),
        # open_meteo_forecast: no report at all (its jobs crashed).
    ]
    status = build_status(ctx, steps)

    assert [(s.id, s.state) for s in status.sources] == [
        ("open_meteo_ensemble", "ok"),
        ("open_meteo_forecast", "down"),
    ]
    assert status.transforms[0].dataset == "ensemble_hourly"
    snowfall = next(k for k in status.kpis if k.id == "snowfall_chance")
    states = {p.key: p.state for p in snowfall.periods}
    assert states["day@2026-12-14"] == "ok"
    assert states["evening@2026-12-14"] == "partial"
    assert states["night@2026-12-14"] == "down"
    onpiste = next(k for k in status.kpis if k.id == "onpiste_powder_chance")
    morning = next(p for p in onpiste.periods if p.key == "morning@2026-12-14")
    assert (morning.state, morning.updated_at) == ("stale", earlier)

    tiles = {(t.tile_id, t.period.key): t.period.state for t in status.tiles["pyrenees"]}
    assert tiles[("snowfall_today", "day@2026-12-14")] == "ok"
    assert tiles[("onpiste_powder", "morning@2026-12-14")] == "stale"
    assert tiles[("offpiste_powder", "morning@2026-12-14")] == "down"
    assert status.state == "down"


def test_finalize_writes_status_and_manifest(ctx: RunContext) -> None:
    _write_gold(ctx, [_result(ctx, "snowfall_chance", "alpha", 0.2)])
    _display(ctx)
    status, keys = finalize_refresh(ctx, [])
    assert status.ski_day == ctx.run_date
    assert keys == ["diamond/manifest.json", status_key()]
    DiamondStatus.model_validate(ctx.storage.read_json(status_key()))
    manifest = build_manifest(ctx)
    assert manifest is not None
    assert manifest.massifs["pyrenees"].archive == "pyrenees/2026-12-14.json"
