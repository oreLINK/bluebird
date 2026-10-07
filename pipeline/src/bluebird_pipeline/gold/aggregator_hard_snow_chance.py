"""KPI ``hard_snow_chance``: hard, icy snow in the morning ("ice and crust").

Snow that melted the day before and refroze overnight is hard and icy in the
morning, until the sun softens it. For each ensemble scenario at ``band``:

1. **Melt** the day before: the maximum temperature from ``melt_start`` to
   ``melt_end`` (local, the day before the ski day) is at least ``melt_min_c``.
2. **Refreeze**: the minimum temperature from ``melt_end`` to the start of
   the slot is at most ``freeze_max_c``.
3. **Still frozen** during the slot: its maximum temperature is at most
   ``frozen_max_c``.
4. **No fresh snow** covering it: less than ``fresh_snow_max_cm`` between
   ``melt_end`` and the end of the slot.

The probability is the share of scenarios meeting all four.
Time slots, and the whole ski day (``ski_start``..``ski_end``) for the
day-grain period ``day``.
"""

from __future__ import annotations

from datetime import UTC
from typing import ClassVar

import polars as pl
from pydantic import Field

from ..config import Band, LocalTime, StationRef, parse_local_time
from ..context import PeriodInstance, RunContext
from ._ensemble import member_table, quantile, share
from ._whiteout import SkiHours, day_or_slot
from .base import Aggregator, AggregatorParams, KpiResult, register_aggregator


class HardSnowParams(SkiHours):
    ski_start: LocalTime = "09:00"
    ski_end: LocalTime = "11:00"
    band: Band = "mid"
    melt_start: LocalTime = "11:00"
    melt_end: LocalTime = "17:00"
    melt_min_c: float = 2.0
    freeze_max_c: float = -2.0
    frozen_max_c: float = 0.0
    fresh_snow_max_cm: float = Field(default=2.0, ge=0)


@register_aggregator("hard_snow_chance")
class AggregatorHardSnowChance(Aggregator):
    """P(melt the day before, refreeze overnight, still frozen during the slot)."""

    version: ClassVar[str] = "2"
    Params: ClassVar[type[AggregatorParams]] = HardSnowParams
    required_datasets: ClassVar[tuple[str, ...]] = ("ensemble_hourly",)
    params: HardSnowParams

    def compute(self, ctx: RunContext, ref: StationRef, period: PeriodInstance) -> KpiResult | None:
        p = self.params
        slot_start, slot_end = day_or_slot(p, period, ref.massif.tz)
        ensemble = ctx.silver("ensemble_hourly")
        melt_start = self.on_ski_day(ctx, ref, period, parse_local_time(p.melt_start), -1)
        melt_end = self.on_ski_day(ctx, ref, period, parse_local_time(p.melt_end), -1)
        # Polars compares a UTC column with UTC bounds only (CONTEXT.md §8).
        slot_start = slot_start.astimezone(UTC)
        common = {"station_id": ref.id, "band": p.band, "required": ["temperature_c"]}
        melt = member_table(
            ensemble, **common, start=melt_start, end=melt_end,
            aggs={"melt_max": pl.col("temperature_c").max()},
        )  # fmt: skip
        night = member_table(
            ensemble, **common, start=melt_end, end=slot_start,
            aggs={"night_min": pl.col("temperature_c").min()},
        )  # fmt: skip
        slot = member_table(
            ensemble,
            station_id=ref.id,
            band=p.band,
            start=melt_end,
            end=slot_end,
            aggs={
                "fresh_snow": pl.col("snowfall_cm").sum(),
                "slot_max": pl.col("temperature_c").filter(pl.col("time_utc") > slot_start).max(),
            },
            required=["temperature_c", "snowfall_cm"],
        )
        keys = ["model", "member"]
        members = melt.join(night, on=keys).join(slot, on=keys)
        if members.is_empty():
            return None
        icy = (
            (pl.col("melt_max") >= p.melt_min_c)
            & (pl.col("night_min") <= p.freeze_max_c)
            & (pl.col("slot_max") <= p.frozen_max_c)
            & (pl.col("fresh_snow") < p.fresh_snow_max_cm)
        )
        return self.result(
            ctx,
            ref,
            period,
            probability=share(members, icy),
            members=members.height,
            window_start=melt_start,
            window_end=slot_end,
            drivers={
                "melt_max_c_p50": quantile(members["melt_max"], 0.5, 1),
                "night_min_c_p50": quantile(members["night_min"], 0.5, 1),
                "members": members.height,
            },
        )
