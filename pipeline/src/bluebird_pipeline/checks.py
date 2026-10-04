"""Checks that need the plugin registries (beyond pure configuration checks)."""

from __future__ import annotations

from pydantic import ValidationError

from .bronze.base import EXTRACTORS
from .config import Config
from .gold.base import AGGREGATORS
from .registry import RegistryError, load_plugins
from .silver.base import TRANSFORMERS


def plugin_errors(config: Config) -> list[str]:
    """Return every reference from the configuration to a missing or misconfigured plugin."""
    load_plugins()
    errors: list[str] = []
    # Silver datasets each kind of KPI can read: live KPIs read the datasets of the
    # day (daily sources), historical KPIs the season archive (season sources).
    datasets: dict[str, set[str]] = {"live": set(), "historical": set()}

    for source in config.sources:
        try:
            EXTRACTORS.get(source.extractor).Params.model_validate(source.params)
        except RegistryError as exc:
            errors.append(f"source '{source.id}': {exc}")
        except ValidationError as exc:
            errors.append(f"source '{source.id}' params: {exc}")
        try:
            transformer = TRANSFORMERS.get(source.transformer)
        except RegistryError as exc:
            errors.append(f"source '{source.id}': {exc}")
            continue
        if source.schedule == "reference" and transformer.reference_suffix is None:
            errors.append(
                f"source '{source.id}' has schedule 'reference' but transformer "
                f"'{source.transformer}' does not produce reference files"
            )
        if source.enabled and source.schedule == "daily":
            datasets["live"].add(transformer.dataset)
        if source.enabled and source.schedule == "season":
            datasets["historical"].add(transformer.dataset)

    for kpi in config.kpis:
        try:
            aggregator = AGGREGATORS.get(kpi.aggregator)
        except RegistryError as exc:
            errors.append(f"KPI '{kpi.id}': {exc}")
            continue
        try:
            aggregator.Params.model_validate(kpi.params)
        except ValidationError as exc:
            errors.append(f"KPI '{kpi.id}' params: {exc}")
        if aggregator.kind != kpi.kind:
            errors.append(
                f"KPI '{kpi.id}' is {kpi.kind} but aggregator '{kpi.aggregator}' "
                f"computes {aggregator.kind} KPIs"
            )
            continue
        if kpi.enabled:
            schedule = "daily" if kpi.kind == "live" else "season"
            for dataset in aggregator.required_datasets:
                if dataset not in datasets[kpi.kind]:
                    errors.append(
                        f"KPI '{kpi.id}' needs silver dataset '{dataset}', "
                        f"which no enabled {schedule} source produces"
                    )
    return errors
