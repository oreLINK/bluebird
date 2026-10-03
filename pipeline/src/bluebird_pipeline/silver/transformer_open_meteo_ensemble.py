"""Silver dataset ``ensemble_hourly``: one row per station, band, model, member, hour."""

from __future__ import annotations

from typing import Any, ClassVar

import polars as pl

from ..bronze.base import BronzeBatch
from ..context import RunContext
from ._open_meteo import SCHEMA, parse_batch
from .base import Transformer, register_transformer


@register_transformer("open_meteo_ensemble")
class TransformerOpenMeteoEnsemble(Transformer):
    """Normalise Open-Meteo ensemble members (control run = member 0)."""

    dataset: ClassVar[str] = "ensemble_hourly"
    schema: ClassVar[dict[str, Any]] = SCHEMA

    def transform(self, batch: BronzeBatch, ctx: RunContext) -> pl.DataFrame:
        frame = self.conform(parse_batch(batch))
        return frame.sort("station_id", "band", "model", "member", "time_utc")
