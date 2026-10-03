"""KPI ``snowfall_chance``: probability that it snows during the ski day.

Model: share of ensemble members whose total snowfall over the day window
(default 08:00-17:00 local) reaches ``threshold_cm`` at the chosen band.
"""

from __future__ import annotations

import logging
from typing import ClassVar

import polars as pl
from pydantic import Field, model_validator

from ..config import Band, LocalTime, parse_local_time
from ..context import RunContext
from ._ensemble import member_window, quantile
from .base import Aggregator, AggregatorParams, DriverValue, KpiResult, register_aggregator

log = logging.getLogger(__name__)


class SnowfallChanceParams(AggregatorParams):
    band: Band = "mid"
    window_start: LocalTime = "08:00"
    window_end: LocalTime = "17:00"
    threshold_cm: float = Field(default=1.0, gt=0)

    @model_validator(mode="after")
    def _window_order(self) -> SnowfallChanceParams:
        if parse_local_time(self.window_end) <= parse_local_time(self.window_start):
            raise ValueError("window_end must be after window_start")
        return self


@register_aggregator("snowfall_chance")
class AggregatorSnowfallChance(Aggregator):
    """P(snowfall over the day window >= threshold)."""

    version: ClassVar[str] = "1"
    Params: ClassVar[type[AggregatorParams]] = SnowfallChanceParams
    required_datasets: ClassVar[tuple[str, ...]] = ("ensemble_hourly",)
    params: SnowfallChanceParams

    def aggregate(self, ctx: RunContext) -> list[KpiResult]:
        ensemble = ctx.silver("ensemble_hourly")
        deterministic = ctx.silver_optional("forecast_hourly")
        p = self.params
        results: list[KpiResult] = []
        for ref in ctx.stations():
            start = ctx.local_datetime(ref.massif, parse_local_time(p.window_start))
            end = ctx.local_datetime(ref.massif, parse_local_time(p.window_end))
            window = {"station_id": ref.id, "band": p.band, "start": start, "end": end}
            totals = member_window(ensemble, **window, column="snowfall_cm", how="sum")
            if totals.is_empty():
                log.warning("%s: no complete ensemble data for %s", self.kpi.id, ref.id)
                continue
            snow = totals["value"]
            drivers: dict[str, DriverValue] = {
                "snow_cm_p50": quantile(snow, 0.5),
                "snow_cm_p90": quantile(snow, 0.9),
                "members": len(snow),
            }
            if deterministic is not None:
                det = member_window(deterministic, **window, column="snowfall_cm", how="sum")
                if not det.is_empty():
                    drivers["deterministic_snow_cm"] = round(float(det["value"].mean()), 1)
            results.append(
                self.result(
                    ctx,
                    ref,
                    probability=float((snow >= p.threshold_cm).cast(pl.Float64).mean()),
                    members=len(snow),
                    window_start=start,
                    window_end=end,
                    drivers=drivers,
                )
            )
        return results
