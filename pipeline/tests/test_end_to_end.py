"""Full bronze -> diamond run against mocked Open-Meteo APIs."""

from __future__ import annotations

from datetime import datetime

import httpx
from _factories import default_values, open_meteo_transport

from bluebird_pipeline.cli import main
from bluebird_pipeline.context import RunContext
from bluebird_pipeline.diamond.models import DiamondMassifDaily
from bluebird_pipeline.runner import LAYERS, run_pipeline


def _no_throttle(ctx: RunContext):
    return [
        s.model_copy(update={"params": {**s.params, "min_interval_s": 0}})
        for s in ctx.config.enabled_sources(schedule="daily")
    ]


def test_all_layers_produce_a_valid_diamond_payload(ctx: RunContext) -> None:
    http = httpx.Client(transport=open_meteo_transport())
    report = run_pipeline(ctx, list(LAYERS), _no_throttle(ctx), http=http)

    assert report.errors == []
    for layer in LAYERS:
        assert report.wrote_layer(layer), layer
    payload = DiamondMassifDaily.model_validate(
        ctx.storage.read_json("diamond/pyrenees/latest.json")
    )
    assert set(payload.kpis) == {
        "snowfall_chance",
        "offpiste_powder_chance",
        "onpiste_powder_chance",
    }
    snowfall = payload.kpis["snowfall_chance"].ranking
    # Default synthetic weather: 0.4 cm/h all day in every member -> certain snowfall.
    assert all(entry.probability == 1.0 for entry in snowfall)
    assert snowfall[0].members == 91
    assert snowfall[0].drivers["deterministic_snow_cm"] == 3.6  # 9 h x 0.4 cm


def test_a_failing_source_does_not_stop_the_run(ctx: RunContext) -> None:
    ok = open_meteo_transport(default_values)

    def handler(request: httpx.Request) -> httpx.Response:
        if "ensemble" not in request.url.host:
            return httpx.Response(400, json={"reason": "broken"})
        return ok.handle_request(request)

    http = httpx.Client(transport=httpx.MockTransport(handler))
    report = run_pipeline(ctx, list(LAYERS), _no_throttle(ctx), http=http)

    assert any(e.startswith("bronze/open_meteo_forecast") for e in report.errors)
    assert report.wrote_layer("diamond")  # KPIs only need the ensemble


def test_cli_validate_and_schema_check() -> None:
    assert main(["validate"]) == 0
    assert main(["schemas", "--check"]) == 0


def test_cli_rejects_unknown_source(tmp_path, capsys) -> None:
    code = main(["run", "--source", "nope", "--data-dir", str(tmp_path), "--date", "2026-12-14"])
    assert code == 2
    assert "unknown source(s): nope" in capsys.readouterr().err


def test_run_date_defaults_to_local_today(ctx: RunContext) -> None:
    # 23:30 UTC on Dec 13 is already Dec 14 in Paris.
    late = RunContext.create(
        ctx.config, ctx.storage, now=datetime.fromisoformat("2026-12-13T23:30:00+00:00")
    )
    assert late.run_date.isoformat() == "2026-12-14"


def test_demo_data_covers_every_kpi(repo_config, tmp_path) -> None:
    from bluebird_pipeline.demo import build_demo

    report = build_demo(repo_config, tmp_path)
    assert report.errors == []
    payload = DiamondMassifDaily.model_validate_json(
        (tmp_path / "diamond" / "pyrenees" / "latest.json").read_text(encoding="utf-8")
    )
    assert len(payload.kpis) == 3
    probabilities = [e.probability for e in payload.kpis["snowfall_chance"].ranking]
    assert max(probabilities) > min(probabilities)  # rankings are not flat


def test_cli_refuses_to_fetch_live_data_for_another_date(tmp_path, capsys) -> None:
    code = main(["run", "--date", "2020-01-01", "--data-dir", str(tmp_path)])
    assert code == 2
    assert "cannot be used with the bronze layer" in capsys.readouterr().err
