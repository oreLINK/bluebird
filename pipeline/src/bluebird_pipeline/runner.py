"""Orchestrate the four layers: bronze -> silver -> gold -> diamond.

Failures are isolated: a failing source, KPI or displayer is logged and
reported, and the run continues with whatever data is available. The CLI
decides the exit code from the :class:`RunReport`.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import httpx

from .bronze.base import EXTRACTORS, BronzeBatch, default_http_client
from .config import Source
from .context import RunContext
from .diamond.base import DISPLAYERS
from .gold.base import AGGREGATORS, KpiResult, results_to_frame
from .registry import load_plugins
from .silver.base import TRANSFORMERS
from .storage import bronze_key, gold_key, latest_key, silver_key
from .storage.keys import bronze_prefix

log = logging.getLogger(__name__)

LAYERS = ("bronze", "silver", "gold", "diamond")


@dataclass
class RunReport:
    """What a run wrote and what failed."""

    written: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def wrote(self, key: str) -> None:
        log.info("wrote %s", key)
        self.written.append(key)

    def failed(self, message: str) -> None:
        log.error(message)
        self.errors.append(message)

    def wrote_layer(self, layer: str) -> bool:
        return any(key.startswith(f"{layer}/") for key in self.written)


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
        except Exception as exc:
            report.failed(f"bronze/{source.id}: {exc}")


def run_silver(ctx: RunContext, sources: list[Source], report: RunReport) -> None:
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
        except Exception as exc:
            report.failed(f"silver/{source.id}: {exc}")
    ctx.invalidate_silver()


def run_gold(ctx: RunContext, report: RunReport) -> None:
    results: list[KpiResult] = []
    for kpi in ctx.config.enabled_kpis():
        try:
            aggregator = AGGREGATORS.get(kpi.aggregator)(kpi)
            kpi_results = aggregator.aggregate(ctx)
            log.info("gold/%s: %d station result(s)", kpi.id, len(kpi_results))
            results.extend(kpi_results)
        except Exception as exc:
            report.failed(f"gold/{kpi.id}: {exc}")
    if not results:
        report.failed("gold: no KPI result, previous gold data left untouched")
        return
    key = gold_key(ctx.run_date)
    ctx.storage.write_parquet(key, results_to_frame(results, ctx.run_id, ctx.generated_at))
    report.wrote(key)


def run_diamond(ctx: RunContext, report: RunReport) -> None:
    for displayer_id, displayer_cls in DISPLAYERS.items():
        try:
            for artifact in displayer_cls().display(ctx):
                ctx.storage.write_json(artifact.key, artifact.payload.model_dump(mode="json"))
                report.wrote(artifact.key)
        except Exception as exc:
            report.failed(f"diamond/{displayer_id}: {exc}")


def run_pipeline(
    ctx: RunContext,
    layers: list[str],
    sources: list[Source],
    http: httpx.Client | None = None,
) -> RunReport:
    """Run ``layers`` in medallion order and return a report."""
    load_plugins()
    report = RunReport()
    log.info(
        "run %s for %s, layers=%s, sources=%s",
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
        run_gold(ctx, report)
    if "diamond" in layers:
        run_diamond(ctx, report)
    return report
