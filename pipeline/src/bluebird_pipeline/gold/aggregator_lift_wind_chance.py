"""KPI ``lift_wind_chance``: wind strong enough to stop the top lifts.

Lifts slow down or stop in strong gusts (chairlifts often from 60-80 km/h).
The ensemble has the mean wind only, not the gusts: for each scenario at
``band`` (the summit), the slot is windy when at least ``min_hours`` of its
hours have a mean wind of ``wind_min_kmh`` or more (gusts are usually 1.5 to
2 times the mean wind in the mountains).
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
from ._whiteout import SkiHours, day_or_slot
from .base import Aggregator, AggregatorParams, KpiResult, register_aggregator


class LiftWindParams(SkiHours):
    band: Band = "summit"
    wind_min_kmh: float = Field(default=45.0, gt=0)
    min_hours: int = Field(default=1, ge=1, le=24)


@register_aggregator("lift_wind_chance")
class AggregatorLiftWindChance(Aggregator):
    """P(at least ``min_hours`` hours of mean wind >= ``wind_min_kmh`` in the slot)."""

    version: ClassVar[str] = "2"
    Params: ClassVar[type[AggregatorParams]] = LiftWindParams
    required_datasets: ClassVar[tuple[str, ...]] = ("ensemble_hourly",)
    params: LiftWindParams

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
                "windy_hours": (pl.col("wind_speed_kmh") >= p.wind_min_kmh).sum(),
                "max_wind": pl.col("wind_speed_kmh").max(),
            },
            required=["wind_speed_kmh"],
        )
        if members.is_empty():
            return None
        return self.result(
            ctx,
            ref,
            period,
            probability=share(members, pl.col("windy_hours") >= p.min_hours),
            members=members.height,
            window_start=slot_start,
            window_end=slot_end,
            drivers={
                "max_wind_kmh_p10": quantile(members["max_wind"], 0.1, 0),
                "max_wind_kmh_p50": quantile(members["max_wind"], 0.5, 0),
                "max_wind_kmh_p90": quantile(members["max_wind"], 0.9, 0),
                "members": members.height,
            },
        )
