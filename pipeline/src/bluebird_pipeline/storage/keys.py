"""Key conventions of each medallion layer.

========  ==========================================================  ==========
Layer     Key                                                         Format
========  ==========================================================  ==========
bronze    ``bronze/{source_id}/{date}/{run_id}.json.gz``              gzip JSON
silver    ``silver/{dataset}/date={date}/{run_id}.parquet``           Parquet
gold      ``gold/kpis/date={date}/{kpi_id}.parquet``                  Parquet
diamond   ``diamond/{massif_id}/latest.json`` and ``{date}.json``     JSON
diamond   ``diamond/manifest.json``                                   JSON
========  ==========================================================  ==========

``run_id`` is a UTC timestamp (``20261214T053000Z``) so keys sort chronologically.
``date`` is the ski day of the run (see ``RunContext``). Gold and diamond keep
one object per ski day: a later run of the same day wins. Gold files written
before periods existed are named ``kpis.parquet`` and are ignored when reading.
"""

from __future__ import annotations

from datetime import date

from .base import Storage


def bronze_key(source_id: str, run_date: date, run_id: str) -> str:
    return f"bronze/{source_id}/{run_date.isoformat()}/{run_id}.json.gz"


def bronze_prefix(source_id: str, run_date: date) -> str:
    return f"bronze/{source_id}/{run_date.isoformat()}"


def silver_key(dataset: str, run_date: date, run_id: str) -> str:
    return f"silver/{dataset}/date={run_date.isoformat()}/{run_id}.parquet"


def silver_prefix(dataset: str, run_date: date) -> str:
    return f"silver/{dataset}/date={run_date.isoformat()}"


def gold_key(run_date: date, kpi_id: str) -> str:
    return f"gold/kpis/date={run_date.isoformat()}/{kpi_id}.parquet"


def diamond_key(massif_id: str | None, name: str) -> str:
    """``diamond/{massif_id}/{name}.json``, or ``diamond/{name}.json`` without massif."""
    if massif_id is None:
        return f"diamond/{name}.json"
    return f"diamond/{massif_id}/{name}.json"


def status_key() -> str:
    return "diamond/status.json"


def latest_key(storage: Storage, prefix: str, suffix: str) -> str | None:
    """Return the last key (lexicographically) under ``prefix`` ending with ``suffix``."""
    keys = [key for key in storage.list(prefix) if key.endswith(suffix)]
    return keys[-1] if keys else None
