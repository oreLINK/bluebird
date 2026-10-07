"""KPI ``mild_day_chance``: a mild, sunny and calm ski day (picnic weather).

For each ensemble scenario at ``band``, over the ski hours
(``ski_start``..``ski_end``): the maximum temperature reaches ``temp_min_c``,
the maximum wind stays at or below ``wind_max_kmh`` and at least
``min_sunny_hours`` hours are sunny (the sunny hour rule of the bluebird
day). Only the whole-day period (``day``: today and tomorrow).
"""

from __future__ import annotations

from typing import ClassVar

import polars as pl
from pydantic import Field, model_validator

from ..config import Band, StationRef
from ..context import PeriodInstance, RunContext
from ._ensemble import member_table, quantile, share
from ._whiteout import SkiHours, clear_sky_expr, sunny_hour_expr
from .base import Aggregator, AggregatorParams, KpiResult, register_aggregator


class MildDayParams(SkiHours):
    band: Band = "mid"
    temp_min_c: float = 5.0
    wind_max_kmh: float = Field(default=20.0, gt=0)
    cloud_max_pct: float = Field(default=30.0, ge=0, le=100)
    clear_sky_index_min: float = Field(default=0.6, gt=0, le=1)
    min_sunny_hours: int = Field(default=5, ge=1, le=24)

    @model_validator(mode="after")
    def _sunny_hours(self) -> MildDayParams:
        if self.min_sunny_hours > self.ski_hours:
            raise ValueError("min_sunny_hours exceeds the ski hours")
        return self


@register_aggregator("mild_day_chance")
class AggregatorMildDayChance(Aggregator):
    """P(warm enough, calm and sunny over the ski hours)."""

    Params: ClassVar[type[AggregatorParams]] = MildDayParams
    required_datasets: ClassVar[tuple[str, ...]] = ("ensemble_hourly",)
    params: MildDayParams

    def compute(self, ctx: RunContext, ref: StationRef, period: PeriodInstance) -> KpiResult | None:
        if not period.period.native_window:
            return None
        p = self.params
        start, end = p.ski_window(period.ski_day, ref.massif.tz)
        clear_sky = clear_sky_expr("time_utc", ref.station.lat, ref.station.lon)
        sunny = sunny_hour_expr(p.cloud_max_pct, p.clear_sky_index_min, clear_sky)
        members = member_table(
            ctx.silver("ensemble_hourly"),
            station_id=ref.id,
            band=p.band,
            start=start,
            end=end,
            columns=[sunny.fill_null(False).alias("sunny")],
            aggs={
                "max_temp": pl.col("temperature_c").max(),
                "max_wind": pl.col("wind_speed_kmh").max(),
                "sunny_hours": pl.col("sunny").sum(),
            },
            required=["temperature_c", "wind_speed_kmh", "cloud_cover_pct", "shortwave_wm2"],
        )
        if members.is_empty():
            return None
        mild = (
            (pl.col("max_temp") >= p.temp_min_c)
            & (pl.col("max_wind") <= p.wind_max_kmh)
            & (pl.col("sunny_hours") >= p.min_sunny_hours)
        )
        return self.result(
            ctx,
            ref,
            period,
            probability=share(members, mild),
            members=members.height,
            window_start=start,
            window_end=end,
            drivers={
                "max_temp_c_p50": quantile(members["max_temp"], 0.5, 1),
                "sunny_hours_p50": quantile(members["sunny_hours"].cast(pl.Float64), 0.5, 0),
                "members": members.height,
            },
        )
