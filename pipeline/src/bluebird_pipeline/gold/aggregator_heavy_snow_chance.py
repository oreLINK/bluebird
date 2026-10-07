"""KPI ``heavy_snow_chance``: wet, heavy "soup" snow during a time slot.

Snow turns heavy and sticky when the air warms well above freezing, or when
snow falls close to 0 °C. For each ensemble scenario at ``band``, the slot is
heavy when its maximum temperature reaches ``warm_min_c``, or when at least
``wet_snow_min_cm`` of snow falls at temperatures of ``wet_snow_min_c`` or
more. Time slots only.
"""

from __future__ import annotations

from typing import ClassVar

import polars as pl
from pydantic import Field

from ..config import Band, StationRef
from ..context import PeriodInstance, RunContext
from ._ensemble import member_table, quantile, share
from .base import Aggregator, AggregatorParams, KpiResult, register_aggregator


class HeavySnowParams(AggregatorParams):
    band: Band = "mid"
    warm_min_c: float = 4.0
    wet_snow_min_c: float = 0.5
    wet_snow_min_cm: float = Field(default=1.0, gt=0)


@register_aggregator("heavy_snow_chance")
class AggregatorHeavySnowChance(Aggregator):
    """P(warm slot, or wet snowfall near 0 °C)."""

    Params: ClassVar[type[AggregatorParams]] = HeavySnowParams
    required_datasets: ClassVar[tuple[str, ...]] = ("ensemble_hourly",)
    params: HeavySnowParams

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
            aggs={
                "max_temp": pl.col("temperature_c").max(),
                "wet_snow": pl.col("snowfall_cm")
                .filter(pl.col("temperature_c") >= p.wet_snow_min_c)
                .sum(),
            },
            required=["temperature_c", "snowfall_cm"],
        )
        if members.is_empty():
            return None
        heavy = (pl.col("max_temp") >= p.warm_min_c) | (pl.col("wet_snow") >= p.wet_snow_min_cm)
        return self.result(
            ctx,
            ref,
            period,
            probability=share(members, heavy),
            members=members.height,
            window_start=period.start,
            window_end=period.end,
            drivers={
                "max_temp_c_p50": quantile(members["max_temp"], 0.5, 1),
                "members": members.height,
            },
        )
