"""KPI ``sunset_chance``: a visible sunset from the top of the ski area.

The sunset time of the ski day is computed for the resort (NOAA solar
position, flat horizon). For each ensemble scenario at ``band`` (the summit),
the total cloud cover over the hour of the sunset, the ``hours_before`` hours
before it and the ``hours_after`` hours after it must average at most
``cloud_max_pct``. Model cloud cover describes the whole air column, so a
sea of clouds below the summit counts as cloud. Only for the ``sunset``
period (native window: shown during the day, today and tomorrow).
"""

from __future__ import annotations

from datetime import timedelta
from typing import ClassVar

import polars as pl
from pydantic import Field

from ..config import Band, StationRef
from ..context import PeriodInstance, RunContext
from ._conditions import sunset_utc
from ._ensemble import member_table, quantile, share
from .base import Aggregator, AggregatorParams, KpiResult, register_aggregator


class SunsetParams(AggregatorParams):
    band: Band = "summit"
    hours_before: int = Field(default=1, ge=0, le=3)
    hours_after: int = Field(default=1, ge=0, le=3)
    cloud_max_pct: float = Field(default=40.0, ge=0, le=100)


@register_aggregator("sunset_chance")
class AggregatorSunsetChance(Aggregator):
    """P(mean cloud cover around the sunset <= ``cloud_max_pct``)."""

    Params: ClassVar[type[AggregatorParams]] = SunsetParams
    required_datasets: ClassVar[tuple[str, ...]] = ("ensemble_hourly",)
    params: SunsetParams

    def compute(self, ctx: RunContext, ref: StationRef, period: PeriodInstance) -> KpiResult | None:
        if not period.period.native_window:
            return None
        p = self.params
        sunset = sunset_utc(period.ski_day, ref.station.lat, ref.station.lon)
        # Whole hours: the hour containing the sunset, ``hours_before`` before it and
        # ``hours_after`` after it (Open-Meteo values describe the hour ending at them).
        hour = sunset.replace(minute=0, second=0, microsecond=0)
        start = hour - timedelta(hours=p.hours_before)
        end = hour + timedelta(hours=1 + p.hours_after)
        members = member_table(
            ctx.silver("ensemble_hourly"),
            station_id=ref.id,
            band=p.band,
            start=start,
            end=end,
            aggs={"cloud": pl.col("cloud_cover_pct").mean()},
            required=["cloud_cover_pct"],
        )
        if members.is_empty():
            return None
        local = sunset.astimezone(ref.massif.tz)
        return self.result(
            ctx,
            ref,
            period,
            probability=share(members, pl.col("cloud") <= p.cloud_max_pct),
            members=members.height,
            window_start=start.astimezone(ref.massif.tz),
            window_end=end.astimezone(ref.massif.tz),
            drivers={
                "sunset_time": local.strftime("%H:%M"),
                "cloud_pct_p50": quantile(members["cloud"], 0.5, 0),
                "members": members.height,
            },
        )
