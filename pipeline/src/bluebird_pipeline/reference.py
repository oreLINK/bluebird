"""Reference data: slow-changing facts about stations (pistes, lifts, terrain…).

Daily data (weather) is fetched every morning and stored by date. Reference
data is different: it barely changes, so it is fetched rarely and kept.

- Sources with ``schedule: reference`` in ``config/sources.yaml`` are refreshed
  with ``bluebird reference`` (manually, or by the ``Refresh reference data``
  workflow, which opens a pull request to ``dev``).
- The source goes through bronze and silver as usual, then its Transformer
  serialises the silver table into one file per massif:
  ``config/reference/{dataset}/{massif_id}{suffix}``.
- These files are committed to git and reviewed like any configuration.
- Every later run reads them with :meth:`RunContext.reference`, whatever the
  date. Nothing is fetched again until the next refresh.
"""

from __future__ import annotations

import logging

import httpx
import polars as pl

from .bronze.base import BronzeBatch, default_http_client
from .config import Config, Source
from .context import RunContext
from .registry import load_plugins
from .runner import RunReport, run_bronze
from .silver.base import TRANSFORMERS, Transformer
from .storage import LocalStorage, bronze_key, latest_key, silver_key

log = logging.getLogger(__name__)

REFERENCE_DIR = "reference"


def reference_key(dataset: str, massif_id: str, suffix: str) -> str:
    """Path of a reference file relative to the configuration folder."""
    return f"{REFERENCE_DIR}/{dataset}/{massif_id}{suffix}"


def reference_sources(config: Config) -> list[tuple[Source, type[Transformer]]]:
    """Enabled reference sources with their Transformer class."""
    load_plugins()
    return [
        (source, TRANSFORMERS.get(source.transformer))
        for source in config.sources
        if source.enabled and source.schedule == "reference"
    ]


def load_reference(
    config: Config, dataset: str, massif_ids: list[str] | None = None
) -> pl.DataFrame | None:
    """Read the committed reference files of ``dataset`` for the enabled massifs."""
    for _, transformer_cls in reference_sources(config):
        if transformer_cls.dataset != dataset or transformer_cls.reference_suffix is None:
            continue
        frames = []
        for massif in config.enabled_massifs(massif_ids):
            path = config.root / reference_key(dataset, massif.id, transformer_cls.reference_suffix)
            if path.is_file():
                frames.append(transformer_cls.read_reference(path.read_bytes()))
        if not frames:
            return None
        station_ids = [ref.id for ref in config.station_refs(massif_ids)]
        return pl.concat(frames).filter(pl.col("station_id").is_in(station_ids))
    return None


def missing_references(config: Config) -> list[str]:
    """Reference files that do not exist yet, as paths relative to ``config/``."""
    missing = []
    for _, transformer_cls in reference_sources(config):
        if transformer_cls.reference_suffix is None:
            continue
        for massif in config.enabled_massifs():
            key = reference_key(
                transformer_cls.dataset, massif.id, transformer_cls.reference_suffix
            )
            if not (config.root / key).is_file():
                missing.append(key)
    return missing


def refresh_references(
    ctx: RunContext,
    sources: list[Source],
    *,
    fetch: bool = True,
    http: httpx.Client | None = None,
) -> RunReport:
    """Rebuild the reference files of ``sources`` for the massifs of ``ctx``.

    With ``fetch=False`` the latest stored bronze batch is reused (any date),
    which is enough when only the transformation changed. An existing file is
    never overwritten when the fetch or the transformation fails, and a massif
    without any row keeps its previous file.
    """
    load_plugins()
    report = RunReport()
    if fetch:
        client = http or default_http_client()
        try:
            run_bronze(ctx, sources, client, report)
        finally:
            if http is None:
                client.close()

    config_storage = LocalStorage(ctx.config.root)
    for source in sources:
        try:
            transformer = TRANSFORMERS.get(source.transformer)(source)
            suffix = transformer.reference_suffix
            if suffix is None:
                raise TypeError(
                    f"transformer '{source.transformer}' does not produce reference data"
                )
            if fetch:
                key = bronze_key(source.id, ctx.run_date, ctx.run_id)
                if not ctx.storage.exists(key):
                    continue  # the bronze error is already reported
            else:
                key = latest_key(ctx.storage, f"bronze/{source.id}", ".json.gz")
                if key is None:
                    raise FileNotFoundError("no stored bronze batch; run without --no-fetch")
                log.info("reusing %s", key)
            batch = BronzeBatch.model_validate_json(ctx.storage.read_json_gz(key))
            frame = transformer.transform(batch, ctx)
            out = silver_key(transformer.dataset, ctx.run_date, ctx.run_id)
            ctx.storage.write_parquet(out, frame)
            report.wrote(out)

            for massif in ctx.massifs():
                content = transformer.reference_file(frame, massif, ctx)
                ref_key = reference_key(transformer.dataset, massif.id, suffix)
                if content is None:
                    report.failed(f"{ref_key}: no rows, previous file left untouched")
                    continue
                config_storage.write_bytes(ref_key, content)
                report.wrote(ref_key)
        except Exception as exc:
            report.failed(f"reference/{source.id}: {exc}")
    return report
