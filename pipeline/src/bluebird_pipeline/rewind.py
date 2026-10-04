"""Rewind: the review of a closed ski season, ranked on historical KPIs.

A Rewind (``config/rewinds.yaml``) names a season (``start``..``end``, local
days included), its massifs and its historical KPIs. ``bluebird rewind``:

1. fetches the season archive of every ``schedule: season`` source (bronze),
   once the season is over;
2. normalises it (silver ``season_hourly``) and writes it, per massif, to the
   committed file ``config/rewind/{rewind_id}/{massif_id}.hourly.parquet``;
3. computes the historical KPIs from that committed file (gold, in the data
   folder);
4. writes the ranked payload ``config/rewind/{rewind_id}/{massif_id}.json``,
   which the site bundles at build time.

With ``fetch=False`` steps 1–2 are skipped and the KPIs are recomputed from
the committed hourly files: no network call. Several season sources can feed
the hourly file (e.g. AROME snowfall, ICON snow depth, AROME humidity and
light). Rows are keyed by station, point, model and hour; a source owns the
columns of its variables. Fetching only some sources (``only``) replaces their
columns in the committed file and keeps every other column, so adding a
variable later only costs the new source's calls. Like reference data, these files
are refreshed by a workflow that opens a pull request, never by the daily run,
and an existing file is never overwritten when its massif has no rows.
"""

from __future__ import annotations

import logging
from datetime import date

import httpx
import polars as pl

from .bronze.base import BronzeBatch, default_http_client
from .config import Config, Rewind, Source
from .context import RunContext
from .diamond.displayer_rewind import DisplayerRewind
from .gold._season import in_window
from .gold.base import AGGREGATORS, SeasonAggregator, SeasonKpiResult, season_results_to_frame
from .registry import load_plugins
from .runner import RunReport, run_bronze
from .silver.base import TRANSFORMERS, Transformer
from .storage import LocalStorage, bronze_key, rewind_gold_key, rewind_key, silver_key

log = logging.getLogger(__name__)


def season_sources(config: Config) -> list[tuple[Source, type[Transformer]]]:
    """Enabled season sources with their Transformer class."""
    load_plugins()
    return [
        (source, TRANSFORMERS.get(source.transformer))
        for source in config.sources
        if source.enabled and source.schedule == "season"
    ]


def is_over(rewind: Rewind, today: date) -> bool:
    """A season can be reviewed once its last day is past."""
    return rewind.end < today


def load_season(config: Config, rewind: Rewind, massif_ids: list[str]) -> pl.DataFrame | None:
    """Committed ``season_hourly`` rows of ``rewind`` for ``massif_ids``, or ``None``."""
    frames = []
    seen: set[str] = set()  # several sources share one file (same transformer)
    for _, transformer_cls in season_sources(config):
        suffix = transformer_cls.season_suffix
        if suffix is None:
            continue
        for massif_id in massif_ids:
            key = rewind_key(rewind.id, massif_id, suffix)
            path = config.root / key
            if key not in seen and path.is_file():
                seen.add(key)
                frames.append(transformer_cls.read_season(path.read_bytes()))
    return pl.concat(frames) if frames else None


SEASON_KEY = ("station_id", "point_id", "model", "time_utc")
SEASON_META = ("point_kind", "lat", "lon", "elevation_m")


def merge_columns(existing: pl.DataFrame, new: pl.DataFrame, columns: list[str]) -> pl.DataFrame:
    """Replace ``columns`` of ``existing`` with those of ``new``, row by row.

    Rows are matched on station, point, model and hour; rows found in only one
    table are kept, with nulls for the values the other table would bring.
    """
    key, meta = list(SEASON_KEY), list(SEASON_META)
    left = existing.drop([c for c in columns if c in existing.columns])
    right = new.select(key + meta + columns).rename({m: f"{m}__new" for m in meta})
    merged = left.join(right, on=key, how="full", coalesce=True)
    return merged.with_columns(pl.coalesce(m, f"{m}__new").alias(m) for m in meta).drop(
        [f"{m}__new" for m in meta]
    )


def _store_season(
    ctx: RunContext, rewind: Rewind, sources: list[Source], report: RunReport
) -> None:
    """Silver: transform each season batch and write the committed hourly files."""
    config_storage = LocalStorage(ctx.config.root)
    for source in sources:
        try:
            transformer = TRANSFORMERS.get(source.transformer)(source)
            suffix = transformer.season_suffix
            if suffix is None:
                raise TypeError(f"transformer '{source.transformer}' does not produce season data")
            key = bronze_key(source.id, ctx.run_date, ctx.run_id)
            if not ctx.storage.exists(key):
                continue  # the bronze error is already reported
            batch = BronzeBatch.model_validate_json(ctx.storage.read_json_gz(key))
            frame = transformer.transform(batch, ctx)
            out = silver_key(transformer.dataset, ctx.run_date, ctx.run_id)
            ctx.storage.write_parquet(out, frame)
            report.wrote(out)
            for massif in ctx.massifs():
                season_file = rewind_key(rewind.id, massif.id, suffix)
                path = ctx.config.root / season_file
                rows = frame
                if path.is_file():
                    rows = merge_columns(
                        transformer.read_season(path.read_bytes()),
                        frame,
                        transformer.season_columns(),
                    )
                content = transformer.season_file(rows, massif, ctx)
                if content is None:
                    report.failed(f"{season_file}: no rows, previous file left untouched")
                    continue
                config_storage.write_bytes(season_file, content)
                report.wrote(season_file)
        except Exception as exc:
            report.failed(f"rewind/{source.id}: {exc}")


def _compute_kpis(ctx: RunContext, rewind: Rewind, report: RunReport) -> None:
    """Gold: every historical KPI of the Rewind, from the committed hourly files."""
    massif_ids = [m.id for m in ctx.massifs()]
    hourly = load_season(ctx.config, rewind, massif_ids)
    if hourly is None:
        report.failed(f"rewind {rewind.id}: no season data; run without --no-fetch first")
        return
    windowed = pl.concat(
        [
            in_window(
                hourly.filter(
                    pl.col("station_id").is_in(
                        [r.id for r in ctx.stations() if r.massif.id == massif.id]
                    )
                ),
                rewind,
                massif.tz,
            )
            for massif in ctx.massifs()
        ]
    )
    results: list[SeasonKpiResult] = []
    kpis = {k.id: k for k in ctx.config.enabled_kpis(kind="historical")}
    for kpi_id in rewind.kpis:
        kpi = kpis.get(kpi_id)
        if kpi is None:
            continue
        try:
            aggregator = AGGREGATORS.get(kpi.aggregator)(kpi)
            if not isinstance(aggregator, SeasonAggregator):
                raise TypeError(f"aggregator '{kpi.aggregator}' is not a season aggregator")
            kpi_results = aggregator.aggregate(ctx, rewind, windowed)
            log.info("gold/rewind/%s: %d station result(s)", kpi_id, len(kpi_results))
            results.extend(kpi_results)
        except Exception as exc:
            report.failed(f"gold/rewind/{kpi_id}: {exc}")
    if not results:
        report.failed(f"rewind {rewind.id}: no KPI result")
        return
    key = rewind_gold_key(rewind.id)
    ctx.storage.write_parquet(key, season_results_to_frame(results))
    report.wrote(key)


def _publish(ctx: RunContext, report: RunReport) -> None:
    """Diamond: the ranked payloads, written next to the hourly files and committed."""
    config_storage = LocalStorage(ctx.config.root)
    try:
        for artifact in DisplayerRewind().display(ctx):
            config_storage.write_json(
                artifact.key, artifact.payload.model_dump(mode="json"), minify=False
            )
            report.wrote(artifact.key)
    except Exception as exc:
        report.failed(f"diamond/rewind: {exc}")


def run_rewind(
    ctx: RunContext,
    *,
    fetch: bool = True,
    only: list[str] | None = None,
    http: httpx.Client | None = None,
) -> RunReport:
    """Build the Rewind of ``ctx.rewind`` for the massifs of ``ctx``.

    ``only`` restricts the fetch to these season source ids (their rows replace
    the previous ones in the committed hourly file; other sources' rows stay).
    """
    rewind = ctx.rewind
    if rewind is None:
        raise ValueError("run_rewind needs a context created with a rewind")
    load_plugins()
    report = RunReport()
    if fetch:
        sources = [
            source for source, _ in season_sources(ctx.config) if not only or source.id in only
        ]
        if not sources:
            report.failed(f"no enabled season source{' among ' + ', '.join(only) if only else ''}")
            return report
        client = http or default_http_client()
        try:
            run_bronze(ctx, sources, client, report)
        finally:
            if http is None:
                client.close()
        _store_season(ctx, rewind, sources, report)
    _compute_kpis(ctx, rewind, report)
    if report.wrote_layer("gold"):
        _publish(ctx, report)
    return report
