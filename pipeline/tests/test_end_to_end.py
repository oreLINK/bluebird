"""Full bronze -> diamond run against mocked Open-Meteo APIs."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import httpx
from _factories import default_values, open_meteo_transport

from bluebird_pipeline.cli import main
from bluebird_pipeline.context import RunContext
from bluebird_pipeline.diamond.models import DiamondMassifDaily, DiamondStatus
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
        "whiteout_chance",
        "bluebird_day_chance",
        "powder_alert_chance",
        "snowmaking_chance",
        "spring_snow_chance",
        "hard_snow_chance",
        "heavy_snow_chance",
        "easy_conditions_chance",
        "sunset_chance",
        "starry_night_chance",
        "sunny_slot_chance",
        "wind_chill_chance",
        "mild_day_chance",
        "chains_chance",
        "lift_wind_chance",
        "wind_slab_chance",
    }
    periods = payload.kpis["snowfall_chance"].periods
    # Run at 05:30 local: every period of the 14th and the 15th, in time order.
    assert len(periods) == 12
    assert [p.key for p in periods[:3]] == [
        "day@2026-12-14",
        "morning@2026-12-14",
        "midday@2026-12-14",
    ]
    snowfall = periods[0].ranking
    # Default synthetic weather: 0.4 cm/h all day in every member -> certain snowfall.
    assert all(entry.probability == 1.0 for entry in snowfall)
    assert snowfall[0].members == 91
    assert snowfall[0].drivers["deterministic_snow_cm"] == 3.6  # 9 h x 0.4 cm
    # Whole day (day-grain) and three time slots, today and tomorrow.
    assert len(payload.kpis["onpiste_powder_chance"].periods) == 8

    # One HTTP request per source, and the status says everything is fresh.
    assert [s.message for s in report.steps if s.layer == "bronze"] == ["1 request(s)"] * 2
    status = DiamondStatus.model_validate(ctx.storage.read_json("diamond/status.json"))
    assert status.state == "ok"
    assert ctx.storage.exists("diamond/manifest.json")


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
    status = DiamondStatus.model_validate(ctx.storage.read_json("diamond/status.json"))
    assert [(s.id, s.state) for s in status.sources] == [
        ("open_meteo_ensemble", "ok"),
        ("open_meteo_forecast", "down"),
    ]
    assert all(k.state == "ok" for k in status.kpis)


def test_cli_validate_and_schema_check() -> None:
    assert main(["validate"]) == 0
    assert main(["schemas", "--check"]) == 0


def test_cli_rejects_unknown_source(tmp_path, capsys) -> None:
    code = main(["run", "--source", "nope", "--data-dir", str(tmp_path), "--date", "2026-12-14"])
    assert code == 2
    assert "unknown source(s): nope" in capsys.readouterr().err


def test_ski_day_starts_at_six_local_time(ctx: RunContext) -> None:
    def ski_day(now: str) -> str:
        return RunContext.create(
            ctx.config, ctx.storage, now=datetime.fromisoformat(now)
        ).run_date.isoformat()

    # 00:30 in Paris on Dec 14 still belongs to the ski day of Dec 13 ("tonight").
    assert ski_day("2026-12-13T23:30:00+00:00") == "2026-12-13"
    assert ski_day("2026-12-14T04:59:00+00:00") == "2026-12-13"  # 05:59 local
    assert ski_day("2026-12-14T05:00:00+00:00") == "2026-12-14"  # 06:00 local
    # Summer time (UTC+2): 06:00 local is 04:00 UTC.
    assert ski_day("2027-04-10T04:00:00+00:00") == "2027-04-10"


def test_run_id_pins_the_run_start(ctx: RunContext) -> None:
    pinned = RunContext.create(ctx.config, ctx.storage, run_id="20261214T170700Z")
    assert pinned.generated_at == datetime(2026, 12, 14, 17, 7, tzinfo=UTC)
    assert pinned.run_id == "20261214T170700Z"
    keys = [i.key for i in pinned.period_instances(pinned.massifs()[0])]
    # 18:07 local: the day-grain sunset (until 22:00) and overnight (until 06:00)
    # periods, then the evening and night slots.
    assert keys[:4] == [
        "sunset@2026-12-14",
        "overnight@2026-12-14",
        "evening@2026-12-14",
        "night@2026-12-14",
    ]


def test_demo_data_covers_every_kpi(repo_config, tmp_path) -> None:
    from bluebird_pipeline.demo import build_demo

    report = build_demo(repo_config, tmp_path)
    assert report.errors == []
    payload = DiamondMassifDaily.model_validate_json(
        (tmp_path / "diamond" / "pyrenees" / "latest.json").read_text(encoding="utf-8")
    )
    assert set(payload.kpis) == {k.id for k in repo_config.enabled_kpis(kind="live")}
    morning = payload.kpis["snowfall_chance"].periods[1]
    probabilities = [e.probability for e in morning.ranking]
    assert max(probabilities) > min(probabilities)  # rankings are not flat
    assert (tmp_path / "diamond" / "status.json").is_file()


def test_cli_refuses_to_fetch_live_data_for_another_date(tmp_path, capsys) -> None:
    code = main(["run", "--date", "2020-01-01", "--data-dir", str(tmp_path)])
    assert code == 2
    assert "cannot be used with the bronze layer" in capsys.readouterr().err


def test_cli_refuses_an_old_run_id_for_live_data(tmp_path, capsys) -> None:
    code = main(["run", "--run-id", "20200101T000000Z", "--data-dir", str(tmp_path)])
    assert code == 2
    err = capsys.readouterr().err
    assert "cannot be used with the bronze layer" in err or "too old" in err


def test_ci_chain_one_job_per_unit(ctx: RunContext, tmp_path, capsys) -> None:
    """Simulate refresh.yml: plan, then gold per KPI, diamond per massif, status.

    Every job only receives the run id chosen by ``plan`` (the 06:00 refresh).
    """
    ctx = RunContext.create(ctx.config, ctx.storage, run_id="20261214T050700Z")
    config_dir = str(ctx.config.root)
    data = str(ctx.storage.root)
    assert main(["--config-dir", config_dir, "plan", "--json", "--run-id", ctx.run_id]) == 0
    plan = json.loads(capsys.readouterr().out)
    assert plan["run_id"] == ctx.run_id
    assert plan["ski_day"] == "2026-12-14"
    assert plan["silver"] == [
        {"source": "open_meteo_ensemble", "dataset": "ensemble_hourly"},
        {"source": "open_meteo_forecast", "dataset": "forecast_hourly"},
    ]
    assert plan["kpis"] == [
        "snowfall_chance",
        "offpiste_powder_chance",
        "onpiste_powder_chance",
        "whiteout_chance",
        "bluebird_day_chance",
        "powder_alert_chance",
        "snowmaking_chance",
        "spring_snow_chance",
        "hard_snow_chance",
        "heavy_snow_chance",
        "easy_conditions_chance",
        "sunset_chance",
        "starry_night_chance",
        "sunny_slot_chance",
        "wind_chill_chance",
        "mild_day_chance",
        "chains_chance",
        "lift_wind_chance",
        "wind_slab_chance",
    ]

    # Bronze and silver for the ensemble only: the forecast jobs "crashed".
    http = httpx.Client(transport=open_meteo_transport())
    sources = [s for s in _no_throttle(ctx) if s.id == "open_meteo_ensemble"]
    run_pipeline(ctx, ["bronze", "silver"], sources, http=http)

    reports = tmp_path / "reports"
    export = tmp_path / "export"
    common = ["--run-id", ctx.run_id, "--data-dir", data]
    for kpi in plan["kpis"]:
        args = ["run", "--layer", "gold", "--kpi", kpi, *common]
        args += ["--report", str(reports / f"gold-{kpi}.json"), "--export", str(export)]
        assert main(["--config-dir", config_dir, *args]) == 0
    assert sorted(p.name for p in (export / "gold/kpis/date=2026-12-14").iterdir()) == [
        f"{k}.parquet" for k in sorted(plan["kpis"])
    ]
    args = ["run", "--layer", "diamond", "--massif", "pyrenees", *common]
    args += ["--report", str(reports / "diamond-pyrenees.json")]
    assert main(["--config-dir", config_dir, *args]) == 0

    summary = tmp_path / "summary.md"
    args = ["status", "--run-id", ctx.run_id, "--data-dir", data, "--reports", str(reports)]
    assert main(["--config-dir", config_dir, *args, "--summary", str(summary)]) == 0
    status = DiamondStatus.model_validate(ctx.storage.read_json("diamond/status.json"))
    # No bronze/silver report was written by the "jobs" above.
    assert {s.state for s in status.sources} == {"down"}
    assert all(k.state == "ok" for k in status.kpis)
    assert "no report: source job failed" in summary.read_text(encoding="utf-8")
