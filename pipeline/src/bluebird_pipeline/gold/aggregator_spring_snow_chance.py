"""KPI ``spring_snow_chance``: "corn" snow softening after a night freeze.

Spring snow is best when the snowpack refreezes overnight, then softens in
the sun. For each ensemble scenario at ``band``:

1. **Night freeze**: the minimum temperature from ``freeze_start`` to
   ``freeze_end`` (local, on the ski day) is at most ``freeze_max_c``.
2. **Softening**: the maximum temperature during the time slot is at least
   ``soften_min_c``.
3. **No fresh snow** on top: less than ``fresh_snow_max_cm`` in the
   ``fresh_snow_hours`` before the slot.

The probability is the share of scenarios meeting all three. Time slots only.
"""

from __future__ import annotations

from datetime import timedelta
from typing import ClassVar

import polars as pl
from pydantic import Field

from ..config import Band, LocalTime, StationRef, parse_local_time
from ..context import PeriodInstance, RunContext
from ._ensemble import member_table, member_window, quantile, share
from .base import Aggregator, AggregatorParams, KpiResult, register_aggregator


class SpringSnowParams(AggregatorParams):
    band: Band = "mid"
    freeze_start: LocalTime = "00:00"
    freeze_end: LocalTime = "08:00"
    freeze_max_c: float = -1.0
    soften_min_c: float = 1.0
    fresh_snow_hours: int = Field(default=24, ge=1, le=48)
    fresh_snow_max_cm: float = Field(default=5.0, ge=0)


@register_aggregator("spring_snow_chance")
class AggregatorSpringSnowChance(Aggregator):
    """P(night freeze, then softening during the slot, without fresh snow)."""

    Params: ClassVar[type[AggregatorParams]] = SpringSnowParams
    required_datasets: ClassVar[tuple[str, ...]] = ("ensemble_hourly",)
    params: SpringSnowParams

    def compute(self, ctx: RunContext, ref: StationRef, period: PeriodInstance) -> KpiResult | None:
        if period.period.native_window:
            return None
        p = self.params
        ensemble = ctx.silver("ensemble_hourly")
        freeze_start = self.on_ski_day(ctx, ref, period, parse_local_time(p.freeze_start))
        freeze_end = self.on_ski_day(ctx, ref, period, parse_local_time(p.freeze_end))
        common = {"station_id": ref.id, "band": p.band}
        night = member_window(
            ensemble, **common, start=freeze_start, end=freeze_end,
            column="temperature_c", how="min", alias="night_min",
        )  # fmt: skip
        slot = member_window(
            ensemble, **common, start=period.start, end=period.end,
            column="temperature_c", how="max", alias="slot_max",
        )  # fmt: skip
        fresh = member_table(
            ensemble,
            **common,
            start=period.start - timedelta(hours=p.fresh_snow_hours),
            end=period.start,
            aggs={"fresh_snow": pl.col("snowfall_cm").sum()},
            required=["snowfall_cm"],
        )
        members = night.join(slot, on=["model", "member"]).join(fresh, on=["model", "member"])
        if members.is_empty():
            return None
        corn = (
            (pl.col("night_min") <= p.freeze_max_c)
            & (pl.col("slot_max") >= p.soften_min_c)
            & (pl.col("fresh_snow") < p.fresh_snow_max_cm)
        )
        return self.result(
            ctx,
            ref,
            period,
            probability=share(members, corn),
            members=members.height,
            window_start=freeze_start,
            window_end=period.end,
            drivers={
                "night_min_c_p50": quantile(members["night_min"], 0.5, 1),
                "slot_max_c_p50": quantile(members["slot_max"], 0.5, 1),
                "members": members.height,
            },
        )
