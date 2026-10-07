"""KPI ``sunny_slot_chance``: a sunny time slot ("grand soleil").

For each ensemble scenario at ``band``, the slot is sunny when at least
``sunny_share_min_pct`` % of its daylight hours are sunny (the sunny hour rule
of the bluebird day: little cloud and strong sunlight for the sun's height).
Hours before sunrise or after sunset do not count; a slot without daylight
is never sunny.
Time slots, and the whole ski day (``ski_start``..``ski_end``) for the
day-grain period ``day``.
"""

from __future__ import annotations

from typing import ClassVar

import polars as pl
from pydantic import Field

from ..config import Band, StationRef
from ..context import PeriodInstance, RunContext
from ._ensemble import member_table, quantile, share
from ._whiteout import MIN_CLEAR_SKY_WM2, SkiHours, clear_sky_expr, day_or_slot, sunny_hour_expr
from .base import Aggregator, AggregatorParams, KpiResult, register_aggregator


class SunnySlotParams(SkiHours):
    band: Band = "mid"
    cloud_max_pct: float = Field(default=30.0, ge=0, le=100)
    clear_sky_index_min: float = Field(default=0.6, gt=0, le=1)
    sunny_share_min_pct: float = Field(default=75.0, gt=0, le=100)


@register_aggregator("sunny_slot_chance")
class AggregatorSunnySlotChance(Aggregator):
    """P(at least ``sunny_share_min_pct`` % of the slot's daylight hours are sunny)."""

    version: ClassVar[str] = "2"
    Params: ClassVar[type[AggregatorParams]] = SunnySlotParams
    required_datasets: ClassVar[tuple[str, ...]] = ("ensemble_hourly",)
    params: SunnySlotParams

    def compute(self, ctx: RunContext, ref: StationRef, period: PeriodInstance) -> KpiResult | None:
        p = self.params
        slot_start, slot_end = day_or_slot(p, period, ref.massif.tz)
        clear_sky = clear_sky_expr("time_utc", ref.station.lat, ref.station.lon)
        daylight = clear_sky >= MIN_CLEAR_SKY_WM2
        members = member_table(
            ctx.silver("ensemble_hourly"),
            station_id=ref.id,
            band=p.band,
            start=slot_start,
            end=slot_end,
            columns=[
                daylight.alias("daylight"),
                sunny_hour_expr(p.cloud_max_pct, p.clear_sky_index_min, clear_sky)
                .fill_null(False)
                .alias("sunny"),
            ],
            aggs={
                "daylight_hours": pl.col("daylight").sum(),
                "sunny_hours": (pl.col("sunny") & pl.col("daylight")).sum(),
            },
            required=["cloud_cover_pct", "shortwave_wm2"],
        )
        if members.is_empty():
            return None
        members = members.with_columns(
            sunny_pct=pl.when(pl.col("daylight_hours") > 0)
            .then(100 * pl.col("sunny_hours") / pl.col("daylight_hours"))
            .otherwise(0.0)
        )
        hours = members["sunny_hours"].cast(pl.Float64)
        return self.result(
            ctx,
            ref,
            period,
            probability=share(
                members,
                (pl.col("daylight_hours") > 0) & (pl.col("sunny_pct") >= p.sunny_share_min_pct),
            ),
            members=members.height,
            window_start=slot_start,
            window_end=slot_end,
            drivers={
                "sunny_pct_p50": quantile(members["sunny_pct"], 0.5, 0),
                "sunny_hours_p10": quantile(hours, 0.1, 0),
                "sunny_hours_p50": quantile(hours, 0.5, 0),
                "sunny_hours_p90": quantile(hours, 0.9, 0),
                "members": members.height,
            },
        )
