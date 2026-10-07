"""KPI ``snowmaking_chance``: a night cold and dry enough for snow cannons.

Snow cannons need a low *wet-bulb* temperature (cold and dry air), about
-2.5 °C or below. For each ensemble scenario at ``band`` (the pistes), the
hours from ``evening_start`` (the evening before the period) to the end of
the night period count; the night is good for snowmaking when at least
``min_hours`` of them have a wet-bulb temperature at or below
``wet_bulb_max_c``. Period ``night`` only.
"""

from __future__ import annotations

from datetime import datetime
from typing import ClassVar

import polars as pl
from pydantic import Field

from ..config import Band, LocalTime, StationRef, parse_local_time
from ..context import PeriodInstance, RunContext
from ._conditions import wet_bulb_expr
from ._ensemble import member_table, quantile, share
from .base import Aggregator, AggregatorParams, KpiResult, register_aggregator


class SnowmakingParams(AggregatorParams):
    band: Band = "mid"
    evening_start: LocalTime = "20:00"
    wet_bulb_max_c: float = -2.5
    min_hours: int = Field(default=6, ge=1, le=24)


@register_aggregator("snowmaking_chance")
class AggregatorSnowmakingChance(Aggregator):
    """P(at least ``min_hours`` hours of wet-bulb <= ``wet_bulb_max_c`` overnight)."""

    Params: ClassVar[type[AggregatorParams]] = SnowmakingParams
    required_datasets: ClassVar[tuple[str, ...]] = ("ensemble_hourly",)
    params: SnowmakingParams

    def compute(self, ctx: RunContext, ref: StationRef, period: PeriodInstance) -> KpiResult | None:
        p = self.params
        # The evening of the ski day the night belongs to (the night starts after midnight).
        start = datetime.combine(
            period.ski_day, parse_local_time(p.evening_start), tzinfo=ref.massif.tz
        )
        members = member_table(
            ctx.silver("ensemble_hourly"),
            station_id=ref.id,
            band=p.band,
            start=start,
            end=period.end,
            columns=[wet_bulb_expr().alias("wet_bulb")],
            aggs={
                "cold_hours": (pl.col("wet_bulb") <= p.wet_bulb_max_c).sum(),
                "min_wet_bulb": pl.col("wet_bulb").min(),
            },
            required=["temperature_c", "relative_humidity_pct"],
        )
        if members.is_empty():
            return None
        hours = members["cold_hours"].cast(pl.Float64)
        return self.result(
            ctx,
            ref,
            period,
            probability=share(members, pl.col("cold_hours") >= p.min_hours),
            members=members.height,
            window_start=start,
            window_end=period.end,
            drivers={
                "cold_hours_p10": quantile(hours, 0.1, 0),
                "cold_hours_p50": quantile(hours, 0.5, 0),
                "cold_hours_p90": quantile(hours, 0.9, 0),
                "wet_bulb_min_c_p50": quantile(members["min_wet_bulb"], 0.5, 1),
                "members": members.height,
            },
        )
