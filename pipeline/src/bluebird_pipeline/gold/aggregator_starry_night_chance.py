"""KPI ``starry_night_chance``: a clear night sky in the evening.

For each ensemble scenario at ``band``, the hours of the evening period with
a total cloud cover of at most ``cloud_max_pct`` are counted; the night is
starry from ``min_clear_hours`` such hours. Period ``evening`` only.
"""

from __future__ import annotations

from typing import ClassVar

import polars as pl
from pydantic import Field

from ..config import Band, StationRef
from ..context import PeriodInstance, RunContext
from ._ensemble import member_table, quantile, share
from .base import Aggregator, AggregatorParams, KpiResult, register_aggregator


class StarryNightParams(AggregatorParams):
    band: Band = "summit"
    cloud_max_pct: float = Field(default=20.0, ge=0, le=100)
    min_clear_hours: int = Field(default=4, ge=1, le=24)


@register_aggregator("starry_night_chance")
class AggregatorStarryNightChance(Aggregator):
    """P(at least ``min_clear_hours`` clear hours during the period)."""

    Params: ClassVar[type[AggregatorParams]] = StarryNightParams
    required_datasets: ClassVar[tuple[str, ...]] = ("ensemble_hourly",)
    params: StarryNightParams

    def compute(self, ctx: RunContext, ref: StationRef, period: PeriodInstance) -> KpiResult | None:
        if period.period.native_window:
            return None
        p = self.params
        members = member_table(
            ctx.silver("ensemble_hourly"),
            station_id=ref.id,
            band=p.band,
            start=period.start,
            end=period.end,
            aggs={"clear_hours": (pl.col("cloud_cover_pct") <= p.cloud_max_pct).sum()},
            required=["cloud_cover_pct"],
        )
        if members.is_empty():
            return None
        return self.result(
            ctx,
            ref,
            period,
            probability=share(members, pl.col("clear_hours") >= p.min_clear_hours),
            members=members.height,
            window_start=period.start,
            window_end=period.end,
            drivers={
                "clear_hours_p50": quantile(members["clear_hours"].cast(pl.Float64), 0.5, 0),
                "members": members.height,
            },
        )
