"""KPI ``heavy_snow_chance``: wet, heavy "soup" snow during a time slot.

Snow turns heavy and sticky when the air warms well above freezing, or when
snow falls close to 0 °C. For each ensemble scenario at ``band``, the slot is
heavy when its maximum temperature reaches ``warm_min_c``, or when at least
``wet_snow_min_cm`` of snow falls at temperatures of ``wet_snow_min_c`` or
more.
Time slots, and the whole ski day (``ski_start``..``ski_end``) for the
day-grain period ``day``.
"""

from __future__ import annotations

from typing import ClassVar

import polars as pl
from pydantic import Field

from ..config import Band, LocalTime, StationRef
from ..context import PeriodInstance, RunContext
from ._ensemble import member_table, quantile, share
from ._whiteout import SkiHours, day_or_slot
from .base import Aggregator, AggregatorParams, KpiResult, register_aggregator


class HeavySnowParams(SkiHours):
    ski_start: LocalTime = "11:00"
    ski_end: LocalTime = "17:00"
    band: Band = "mid"
    warm_min_c: float = 4.0
    wet_snow_min_c: float = 0.5
    wet_snow_min_cm: float = Field(default=1.0, gt=0)


@register_aggregator("heavy_snow_chance")
class AggregatorHeavySnowChance(Aggregator):
    """P(warm slot, or wet snowfall near 0 °C)."""

    version: ClassVar[str] = "2"
    Params: ClassVar[type[AggregatorParams]] = HeavySnowParams
    required_datasets: ClassVar[tuple[str, ...]] = ("ensemble_hourly",)
    params: HeavySnowParams

    def compute(self, ctx: RunContext, ref: StationRef, period: PeriodInstance) -> KpiResult | None:
        p = self.params
        slot_start, slot_end = day_or_slot(p, period, ref.massif.tz)
        members = member_table(
            ctx.silver("ensemble_hourly"),
            station_id=ref.id,
            band=p.band,
            start=slot_start,
            end=slot_end,
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
            window_start=slot_start,
            window_end=slot_end,
            drivers={
                "max_temp_c_p50": quantile(members["max_temp"], 0.5, 1),
                "members": members.height,
            },
        )
