"""Silver dataset ``forecast_hourly``: deterministic forecast per station, band, model, hour.

Shares the ``ensemble_hourly`` schema; ``member`` is always 0.
"""

from __future__ import annotations

from typing import Any, ClassVar

import polars as pl

from ..bronze.base import BronzeBatch
from ..context import RunContext
from ._open_meteo import SCHEMA, parse_batch
from .base import Transformer, register_transformer


@register_transformer("open_meteo_forecast")
class TransformerOpenMeteoForecast(Transformer):
    """Normalise Open-Meteo deterministic forecasts."""

    dataset: ClassVar[str] = "forecast_hourly"
    schema: ClassVar[dict[str, Any]] = SCHEMA

    def transform(self, batch: BronzeBatch, ctx: RunContext) -> pl.DataFrame:
        frame = self.conform(parse_batch(batch))
        return frame.sort("station_id", "band", "model", "time_utc")
