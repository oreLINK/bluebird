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
    datasets: set[str] = set()

    for source in config.sources:
        try:
            EXTRACTORS.get(source.extractor).Params.model_validate(source.params)
        except RegistryError as exc:
            errors.append(f"source '{source.id}': {exc}")
        except ValidationError as exc:
            errors.append(f"source '{source.id}' params: {exc}")
        try:
            transformer = TRANSFORMERS.get(source.transformer)
            if source.enabled:
                datasets.add(transformer.dataset)
        except RegistryError as exc:
            errors.append(f"source '{source.id}': {exc}")

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
        if kpi.enabled:
            for dataset in aggregator.required_datasets:
                if dataset not in datasets:
                    errors.append(
                        f"KPI '{kpi.id}' needs silver dataset '{dataset}', "
                        "which no enabled source produces"
                    )
    return errors
