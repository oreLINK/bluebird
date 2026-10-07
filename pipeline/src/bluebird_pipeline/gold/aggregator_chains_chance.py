"""KPI ``chains_chance``: snow on the access road in the morning (chains needed).

The ensemble samples the resort at mid-mountain and near the summit, not on
its access road. The road is taken at the bottom of the resort (its base
elevation): the mid-mountain temperature is brought down with the standard
lapse rate (:mod:`._conditions`), and the mid-mountain snowfall counts as
snow on the road during the hours when that road temperature is at most
``road_temp_max_c``. For each ensemble scenario, chains are needed when this
snow, from ``since`` the evening before to ``until`` on the ski day (local),
reaches ``threshold_cm``. It says nothing of snow clearing, nor of the legal
duty to carry winter equipment. Only the whole-day period (``day``).
"""

from __future__ import annotations

from datetime import datetime
from typing import ClassVar

import polars as pl
from pydantic import Field

from ..config import LocalTime, StationRef, parse_local_time
from ..context import PeriodInstance, RunContext
from ._conditions import base_temperature_expr
from ._ensemble import member_table, quantile, share
from .base import Aggregator, AggregatorParams, KpiResult, register_aggregator


class ChainsParams(AggregatorParams):
    since: LocalTime = "20:00"
    until: LocalTime = "10:00"
    road_temp_max_c: float = 1.0
    threshold_cm: float = Field(default=2.0, gt=0)


@register_aggregator("chains_chance")
class AggregatorChainsChance(Aggregator):
    """P(snow on the road at the resort's base elevation >= ``threshold_cm``)."""

    Params: ClassVar[type[AggregatorParams]] = ChainsParams
    required_datasets: ClassVar[tuple[str, ...]] = ("ensemble_hourly",)
    params: ChainsParams

    def compute(self, ctx: RunContext, ref: StationRef, period: PeriodInstance) -> KpiResult | None:
        if not period.period.native_window:
            return None
        p = self.params
        tz = ref.massif.tz
        start = self.on_ski_day(ctx, ref, period, parse_local_time(p.since), -1)
        end = datetime.combine(period.ski_day, parse_local_time(p.until), tzinfo=tz)
        road = base_temperature_expr(ref.station.elevation.base)
        members = member_table(
            ctx.silver("ensemble_hourly"),
            station_id=ref.id,
            band="mid",
            start=start,
            end=end,
            columns=[road.alias("road_temp")],
            aggs={
                "road_snow": pl.col("snowfall_cm")
                .filter(pl.col("road_temp") <= p.road_temp_max_c)
                .sum(),
                "road_temp_min": pl.col("road_temp").min(),
            },
            required=["snowfall_cm", "temperature_c"],
        )
        if members.is_empty():
            return None
        return self.result(
            ctx,
            ref,
            period,
            probability=share(members, pl.col("road_snow") >= p.threshold_cm),
            members=members.height,
            window_start=start,
            window_end=end,
            drivers={
                "road_snow_cm_p50": quantile(members["road_snow"], 0.5, 1),
                "road_temp_min_c_p50": quantile(members["road_temp_min"], 0.5, 1),
                "base_m": ref.station.elevation.base,
                "members": members.height,
            },
        )
