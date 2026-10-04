"""Key conventions of each medallion layer.

========  ==========================================================  ==========
Layer     Key                                                         Format
========  ==========================================================  ==========
bronze    ``bronze/{source_id}/{date}/{run_id}.json.gz``              gzip JSON
silver    ``silver/{dataset}/date={date}/{run_id}.parquet``           Parquet
gold      ``gold/kpis/date={date}/kpis.parquet``                      Parquet
diamond   ``diamond/{massif_id}/latest.json`` and ``{date}.json``     JSON
diamond   ``diamond/manifest.json``                                   JSON
gold      ``gold/rewind/{rewind_id}/kpis.parquet`` (Rewind)            Parquet
========  ==========================================================  ==========

Rewind season files are committed under the configuration folder instead:
``rewind/{rewind_id}/{massif_id}.hourly.parquet`` (silver) and
``rewind/{rewind_id}/{massif_id}.json`` (diamond), see :func:`rewind_key`.

``run_id`` is a UTC timestamp (``20261214T053000Z``) so keys sort chronologically.
Gold and diamond keep one object per date: a later run of the same day wins.
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


def gold_key(run_date: date) -> str:
    return f"gold/kpis/date={run_date.isoformat()}/kpis.parquet"


def diamond_key(massif_id: str | None, name: str) -> str:
    """``diamond/{massif_id}/{name}.json``, or ``diamond/{name}.json`` without massif."""
    if massif_id is None:
        return f"diamond/{name}.json"
    return f"diamond/{massif_id}/{name}.json"


def rewind_gold_key(rewind_id: str) -> str:
    return f"gold/rewind/{rewind_id}/kpis.parquet"


def rewind_key(rewind_id: str, massif_id: str, suffix: str) -> str:
    """Committed Rewind file, relative to ``config/``: ``rewind/{id}/{massif}{suffix}``."""
    return f"rewind/{rewind_id}/{massif_id}{suffix}"


def latest_key(storage: Storage, prefix: str, suffix: str) -> str | None:
    """Return the last key (lexicographically) under ``prefix`` ending with ``suffix``."""
    keys = [key for key in storage.list(prefix) if key.endswith(suffix)]
    return keys[-1] if keys else None
