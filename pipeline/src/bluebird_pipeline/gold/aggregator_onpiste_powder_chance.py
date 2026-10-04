"""KPI ``onpiste_powder_chance``: fresh snow on the pistes after grooming.

Snow that falls after the night's grooming covers the pistes with fresh snow.
For a period, the reference time ``T`` is its start, but never before lifts
open (the morning slot is evaluated at opening). Probability = share of
ensemble members whose snowfall over ``(grooming_end, T]`` reaches
``threshold_cm`` at the chosen band.

``grooming_end`` and ``lifts_open`` come from the station configuration. When
``grooming_end`` is later than ``lifts_open`` (e.g. 22:00), it refers to the
previous evening.
"""

from __future__ import annotations

from typing import ClassVar

import polars as pl
from pydantic import Field

from ..config import Band, StationRef
from ..context import PeriodInstance, RunContext
from ._ensemble import member_window, quantile
from .base import Aggregator, AggregatorParams, KpiResult, register_aggregator


class OnpisteParams(AggregatorParams):
    band: Band = "mid"
    threshold_cm: float = Field(default=5.0, gt=0)


@register_aggregator("onpiste_powder_chance")
class AggregatorOnpistePowderChance(Aggregator):
    """P(snowfall between grooming end and the period start >= threshold)."""

    version: ClassVar[str] = "2"
    Params: ClassVar[type[AggregatorParams]] = OnpisteParams
    required_datasets: ClassVar[tuple[str, ...]] = ("ensemble_hourly",)
    params: OnpisteParams

    def compute(self, ctx: RunContext, ref: StationRef, period: PeriodInstance) -> KpiResult | None:
        ensemble = ctx.silver("ensemble_hourly")
        p = self.params
        days_before = -1 if ref.grooming_end > ref.lifts_open else 0
        start = self.on_ski_day(ctx, ref, period, ref.grooming_end, days_before)
        opening = self.on_ski_day(ctx, ref, period, ref.lifts_open)
        end = opening if period.period.native_window else max(opening, period.start)
        if end <= start:
            return None
        totals = member_window(
            ensemble,
            station_id=ref.id,
            band=p.band,
            start=start,
            end=end,
            column="snowfall_cm",
            how="sum",
        )
        if totals.is_empty():
            return None
        snow = totals["value"]
        return self.result(
            ctx,
            ref,
            period,
            probability=float((snow >= p.threshold_cm).cast(pl.Float64).mean()),
            members=len(snow),
            window_start=start,
            window_end=end,
            drivers={
                "snow_after_grooming_cm_p50": quantile(snow, 0.5),
                "snow_after_grooming_cm_p90": quantile(snow, 0.9),
                "window_hours": round((end - start).total_seconds() / 3600),
                "members": len(snow),
            },
        )
