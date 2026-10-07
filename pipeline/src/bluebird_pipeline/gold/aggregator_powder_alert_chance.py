"""KPI ``powder_alert_chance``: a big snowfall from the start of the ski day.

For each ensemble scenario at ``band``, snowfall over the ``hours`` after the
start of the ski day (``start``, local) must reach ``threshold_cm``. Only the
whole-day period (``day``: today and tomorrow); the ensemble is fetched three
days ahead, enough for a 36-hour window from tomorrow morning.
"""

from __future__ import annotations

from datetime import timedelta
from typing import ClassVar

import polars as pl
from pydantic import Field

from ..config import Band, LocalTime, StationRef, parse_local_time
from ..context import PeriodInstance, RunContext
from ._ensemble import member_table, quantile, share
from .base import Aggregator, AggregatorParams, KpiResult, register_aggregator


class PowderAlertParams(AggregatorParams):
    band: Band = "mid"
    start: LocalTime = "06:00"
    hours: int = Field(default=36, ge=6, le=48)
    threshold_cm: float = Field(default=30.0, gt=0)


@register_aggregator("powder_alert_chance")
class AggregatorPowderAlertChance(Aggregator):
    """P(snowfall over ``hours`` from the ski day start >= ``threshold_cm``)."""

    Params: ClassVar[type[AggregatorParams]] = PowderAlertParams
    required_datasets: ClassVar[tuple[str, ...]] = ("ensemble_hourly",)
    params: PowderAlertParams

    def compute(self, ctx: RunContext, ref: StationRef, period: PeriodInstance) -> KpiResult | None:
        if not period.period.native_window:
            return None
        p = self.params
        start = self.on_ski_day(ctx, ref, period, parse_local_time(p.start))
        end = start + timedelta(hours=p.hours)
        members = member_table(
            ctx.silver("ensemble_hourly"),
            station_id=ref.id,
            band=p.band,
            start=start,
            end=end,
            aggs={"snow": pl.col("snowfall_cm").sum()},
            required=["snowfall_cm"],
        )
        if members.is_empty():
            return None
        return self.result(
            ctx,
            ref,
            period,
            probability=share(members, pl.col("snow") >= p.threshold_cm),
            members=members.height,
            window_start=start,
            window_end=end,
            drivers={
                "snow_cm_p10": quantile(members["snow"], 0.1, 0),
                "snow_cm_p50": quantile(members["snow"], 0.5, 0),
                "snow_cm_p90": quantile(members["snow"], 0.9, 0),
                "members": members.height,
            },
        )
