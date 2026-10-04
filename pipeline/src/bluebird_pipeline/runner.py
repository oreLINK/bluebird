"""Orchestrate the four layers: bronze -> silver -> gold -> diamond.

Failures are isolated: a failing source, KPI or massif is logged and reported,
and the run continues with whatever data is available. Each unit (source,
dataset, KPI, massif) records a :class:`~.report.StepReport`; the CLI decides
the exit code from the :class:`RunReport`.

A run can target one unit (``bluebird run --layer gold --kpi snowfall_chance``):
that is how the CI workflow runs one job per source, dataset, KPI and massif.
A full run ends with :func:`~.diamond._status.finalize_refresh`, which writes
``diamond/status.json`` and the manifest; in CI the ``status`` job does it.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import httpx
import polars as pl

from .bronze.base import EXTRACTORS, BronzeBatch, default_http_client
from .config import Kpi, Source
from .context import RunContext
from .diamond.base import DISPLAYERS
from .gold.base import AGGREGATORS, INSTANCE, read_gold, results_to_frame
from .registry import load_plugins
from .report import Layer, ReportFile, State, StepReport, coverage_state
from .silver.base import TRANSFORMERS
from .storage import bronze_key, gold_key, latest_key, silver_key
from .storage.keys import bronze_prefix

log = logging.getLogger(__name__)

LAYERS = ("bronze", "silver", "gold", "diamond")


@dataclass
class RunReport:
    """What a run wrote, what failed, and the state of each unit."""

    written: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    steps: list[StepReport] = field(default_factory=list)

    def wrote(self, key: str) -> None:
        log.info("wrote %s", key)
        self.written.append(key)

    def failed(self, message: str) -> None:
        log.error(message)
        self.errors.append(message)

    def step(
        self,
        layer: Layer,
        unit: str,
        state: State,
        *,
        ok: int | None = None,
        expected: int | None = None,
        message: str | None = None,
    ) -> None:
        self.steps.append(
            StepReport(layer=layer, id=unit, state=state, ok=ok, expected=expected, message=message)
        )

    def wrote_layer(self, layer: str) -> bool:
        return any(key.startswith(f"{layer}/") for key in self.written)

    def to_file(self, ctx: RunContext) -> ReportFile:
        return ReportFile(run_id=ctx.run_id, run_date=ctx.run_date, steps=self.steps)


def run_bronze(
    ctx: RunContext, sources: list[Source], http: httpx.Client, report: RunReport
) -> None:
    for source in sources:
        try:
            extractor = EXTRACTORS.get(source.extractor)(source, http)
            records = extractor.extract(ctx)
            batch = BronzeBatch(
                source_id=source.id, run_id=ctx.run_id, run_date=ctx.run_date, records=records
            )
            key = bronze_key(source.id, ctx.run_date, ctx.run_id)
            ctx.storage.write_json_gz(key, batch.model_dump_json())
            report.wrote(key)
            report.step("bronze", source.id, "ok", message=f"{len(records)} request(s)")
        except Exception as exc:
            report.failed(f"bronze/{source.id}: {exc}")
            report.step("bronze", source.id, "down", message=str(exc))


def run_silver(ctx: RunContext, sources: list[Source], report: RunReport) -> None:
    expected = len(ctx.stations())
    for source in sources:
        try:
            key = latest_key(ctx.storage, bronze_prefix(source.id, ctx.run_date), ".json.gz")
            if key is None:
                raise FileNotFoundError(f"no bronze batch for {ctx.run_date}")
            batch = BronzeBatch.model_validate_json(ctx.storage.read_json_gz(key))
            transformer = TRANSFORMERS.get(source.transformer)(source)
            frame = transformer.transform(batch, ctx)
            out = silver_key(transformer.dataset, ctx.run_date, ctx.run_id)
            ctx.storage.write_parquet(out, frame)
            report.wrote(out)
            ok = frame["station_id"].n_unique() if "station_id" in frame.columns else expected
            report.step(
                "silver",
                source.id,
                coverage_state(ok, expected),
                ok=ok,
                expected=expected,
                message=f"{frame.height} row(s) in {transformer.dataset}",
            )
        except Exception as exc:
            report.failed(f"silver/{source.id}: {exc}")
            report.step("silver", source.id, "down", ok=0, expected=expected, message=str(exc))
    ctx.invalidate_silver()


def _expected_instances(ctx: RunContext, kpi: Kpi) -> dict[tuple[str, object], int]:
    """``(period_id, ski_day) -> station count`` of every visible period of ``kpi``."""
    expected: dict[tuple[str, object], int] = {}
    for massif in ctx.massifs():
        stations = sum(1 for ref in ctx.stations() if ref.massif.id == massif.id)
        for instance in ctx.period_instances(massif, kpi.periods):
            key = (instance.period_id, instance.ski_day)
            expected[key] = expected.get(key, 0) + stations
    return expected


def run_gold_kpi(ctx: RunContext, kpi: Kpi, report: RunReport) -> None:
    """Compute one KPI and write its gold file, keeping earlier values it could not refresh.

    Periods the aggregator could not compute this time (missing silver data, an
    error) keep the rows of the latest run that did; they are flagged ``stale``.
    """
    error: str | None = None
    try:
        results = AGGREGATORS.get(kpi.aggregator)(kpi).aggregate(ctx)
        log.info("gold/%s: %d station-period result(s)", kpi.id, len(results))
    except Exception as exc:
        results = []
        error = str(exc)
        report.failed(f"gold/{kpi.id}: {exc}")

    fresh = results_to_frame(results, ctx.run_id, ctx.generated_at)
    previous = read_gold(ctx, [kpi.id])
    carried = previous.join(fresh.select(INSTANCE).unique(), on=INSTANCE, how="anti")
    merged = pl.concat([fresh, carried]) if not carried.is_empty() else fresh

    expected = _expected_instances(ctx, kpi)
    if merged.is_empty():
        report.failed(f"gold/{kpi.id}: no result and nothing to keep from earlier runs")
        report.step("gold", kpi.id, "down", ok=0, expected=len(expected), message=error)
        return
    key = gold_key(ctx.run_date, kpi.id)
    ctx.storage.write_parquet(key, merged)
    report.wrote(key)

    counts = fresh.group_by("period_id", "forecast_date").agg(pl.col("station_id").n_unique())
    fresh_counts = {(r[0], r[1]): r[2] for r in counts.iter_rows()}
    complete = sum(1 for k, n in expected.items() if fresh_counts.get(k, 0) >= n)
    stale = carried.select(INSTANCE).unique().height
    if stale:
        state: State = "stale"
        message = f"{stale} period(s) kept from an earlier run" + (f": {error}" if error else "")
    else:
        state = coverage_state(complete, len(expected)) if fresh_counts else "down"
        message = error
    report.step("gold", kpi.id, state, ok=complete, expected=len(expected), message=message)


def run_gold(ctx: RunContext, report: RunReport, kpi_ids: list[str] | None = None) -> None:
    for kpi in ctx.config.enabled_kpis(kind="live"):
        if kpi_ids is None or kpi.id in kpi_ids:
            run_gold_kpi(ctx, kpi, report)


def run_diamond(ctx: RunContext, report: RunReport) -> None:
    for displayer_id, displayer_cls in DISPLAYERS.items():
        if displayer_cls.schedule != "daily":
            continue
        try:
            written: set[str] = set()
            for artifact in displayer_cls().display(ctx):
                ctx.storage.write_json(artifact.key, artifact.payload.model_dump(mode="json"))
                report.wrote(artifact.key)
                written.add(artifact.key.split("/")[1])
            for massif in ctx.massifs():
                if massif.id in written:
                    report.step("diamond", massif.id, "ok")
                else:
                    report.step("diamond", massif.id, "down", message="no KPI data to publish")
        except Exception as exc:
            report.failed(f"diamond/{displayer_id}: {exc}")
            for massif in ctx.massifs():
                report.step("diamond", massif.id, "down", message=str(exc))


def finalize(ctx: RunContext, report: RunReport, steps: list[StepReport] | None = None) -> None:
    """Write ``diamond/status.json`` and the manifest from ``steps`` (default: this run's)."""
    from .diamond._status import finalize_refresh

    try:
        _, keys = finalize_refresh(ctx, report.steps if steps is None else steps)
        for key in keys:
            report.wrote(key)
    except Exception as exc:
        report.failed(f"status: {exc}")


def run_pipeline(
    ctx: RunContext,
    layers: list[str],
    sources: list[Source],
    http: httpx.Client | None = None,
    *,
    kpi_ids: list[str] | None = None,
    final: bool | None = None,
) -> RunReport:
    """Run ``layers`` in medallion order and return a report.

    ``final`` (default: when every layer runs) also writes the status and the
    manifest. Targeted runs (one layer, ``kpi_ids``) leave that to the caller.
    """
    load_plugins()
    report = RunReport()
    log.info(
        "run %s for ski day %s, layers=%s, sources=%s",
        ctx.run_id,
        ctx.run_date,
        ",".join(layers),
        ",".join(s.id for s in sources) or "-",
    )
    if "bronze" in layers:
        own_client = http is None
        client = http or default_http_client()
        try:
            run_bronze(ctx, sources, client, report)
        finally:
            if own_client:
                client.close()
    if "silver" in layers:
        run_silver(ctx, sources, report)
    if "gold" in layers:
        run_gold(ctx, report, kpi_ids)
    if "diamond" in layers:
        run_diamond(ctx, report)
    if final if final is not None else (list(layers) == list(LAYERS) and kpi_ids is None):
        finalize(ctx, report)
    return report
