from __future__ import annotations

from datetime import UTC, datetime

import pytest

from bluebird_pipeline.context import RunContext
from bluebird_pipeline.diamond import DISPLAYERS
from bluebird_pipeline.diamond.models import DiamondManifest, DiamondMassifDaily
from bluebird_pipeline.gold.base import KpiResult, results_to_frame
from bluebird_pipeline.storage import gold_key


def _result(kpi_id: str, station_id: str, probability: float) -> KpiResult:
    return KpiResult(
        kpi_id=kpi_id,
        station_id=station_id,
        massif_id="pyrenees",
        forecast_date=datetime(2026, 12, 14).date(),
        probability=probability,
        confidence="high",
        window_start=datetime(2026, 12, 14, 7, tzinfo=UTC),
        window_end=datetime(2026, 12, 14, 16, tzinfo=UTC),
        members=91,
        drivers={"snow_cm_p50": 3.5},
        aggregator=kpi_id,
        aggregator_version="1",
    )


def _write_gold(ctx: RunContext, results: list[KpiResult]) -> None:
    frame = results_to_frame(results, ctx.run_id, ctx.generated_at)
    ctx.storage.write_parquet(gold_key(ctx.run_date), frame)


def test_rankings_are_sorted_and_times_are_local(ctx: RunContext) -> None:
    _write_gold(
        ctx,
        [
            _result("snowfall_chance", "alpha", 0.2),
            _result("snowfall_chance", "beta", 0.8),
            _result("onpiste_powder_chance", "alpha", 0.5),
        ],
    )
    artifacts = DISPLAYERS.get("massif_daily")().display(ctx)
    keys = [a.key for a in artifacts]
    assert keys == [
        "diamond/pyrenees/latest.json",
        "diamond/pyrenees/2026-12-14.json",
        "diamond/manifest.json",
    ]

    payload = artifacts[0].payload
    assert isinstance(payload, DiamondMassifDaily)
    ranking = payload.kpis["snowfall_chance"].ranking
    assert [r.station_id for r in ranking] == ["beta", "alpha"]
    assert ranking[0].window_start.isoformat() == "2026-12-14T08:00:00+01:00"
    assert "offpiste_powder_chance" not in payload.kpis  # no gold rows for it
    assert set(payload.stations) == {"alpha", "beta"}
    assert payload.stations["alpha"].elevation.mid == 2000
    assert {s.id for s in payload.sources} == {"open_meteo_ensemble", "open_meteo_forecast"}

    # Round-trips through JSON exactly as the frontend will read it.
    DiamondMassifDaily.model_validate_json(payload.model_dump_json())


def test_manifest_keeps_other_massifs(ctx: RunContext) -> None:
    ctx.storage.write_json(
        "diamond/manifest.json",
        {
            "schema_version": 1,
            "generated_at": "2026-12-13T05:00:00Z",
            "massifs": {
                "alps": {
                    "forecast_date": "2026-12-13",
                    "generated_at": "2026-12-13T05:00:00Z",
                    "latest": "alps/latest.json",
                    "archive": "alps/2026-12-13.json",
                }
            },
        },
    )
    _write_gold(ctx, [_result("snowfall_chance", "alpha", 0.2)])
    manifest = DISPLAYERS.get("massif_daily")().display(ctx)[-1].payload
    assert isinstance(manifest, DiamondManifest)
    assert set(manifest.massifs) == {"alps", "pyrenees"}


def test_missing_gold_is_an_error(ctx: RunContext) -> None:
    with pytest.raises(FileNotFoundError, match="run the gold layer first"):
        DISPLAYERS.get("massif_daily")().display(ctx)
