"""KPI ``wind_slab_chance``: fresh snow moved by the wind (a warning sign off-piste).

Wind blows fresh snow into slabs on lee slopes, a classic avalanche sign. For
each ensemble scenario at ``band`` (the summit): at least ``fresh_snow_cm`` of
snow fell in the ``lookback_hours`` before ``ski_start`` (local), and the
maximum wind from the start of that window to ``ski_end`` reached
``wind_min_kmh``. This never replaces the avalanche bulletin. Only the
whole-day period (``day``: today and tomorrow).
"""

from __future__ import annotations

from datetime import timedelta
from typing import ClassVar

import polars as pl
from pydantic import Field

from ..config import Band, StationRef
from ..context import PeriodInstance, RunContext
from ._ensemble import member_table, quantile, share
from ._whiteout import SkiHours
from .base import Aggregator, AggregatorParams, KpiResult, register_aggregator


class WindSlabParams(SkiHours):
    band: Band = "summit"
    lookback_hours: int = Field(default=48, ge=6, le=48)
    fresh_snow_cm: float = Field(default=10.0, gt=0)
    wind_min_kmh: float = Field(default=30.0, gt=0)


@register_aggregator("wind_slab_chance")
class AggregatorWindSlabChance(Aggregator):
    """P(fresh snow over ``lookback_hours`` and strong wind since)."""

    Params: ClassVar[type[AggregatorParams]] = WindSlabParams
    required_datasets: ClassVar[tuple[str, ...]] = ("ensemble_hourly",)
    params: WindSlabParams

    def compute(self, ctx: RunContext, ref: StationRef, period: PeriodInstance) -> KpiResult | None:
        if not period.period.native_window:
            return None
        p = self.params
        ski_start, ski_end = p.ski_window(period.ski_day, ref.massif.tz)
        start = ski_start - timedelta(hours=p.lookback_hours)
        common = {"station_id": ref.id, "band": p.band, "start": start}
        snow = member_table(
            ctx.silver("ensemble_hourly"), **common, end=ski_start,
            aggs={"fresh_snow": pl.col("snowfall_cm").sum()}, required=["snowfall_cm"],
        )  # fmt: skip
        wind = member_table(
            ctx.silver("ensemble_hourly"), **common, end=ski_end,
            aggs={"max_wind": pl.col("wind_speed_kmh").max()}, required=["wind_speed_kmh"],
        )  # fmt: skip
        members = snow.join(wind, on=["model", "member"])
        if members.is_empty():
            return None
        slab = (pl.col("fresh_snow") >= p.fresh_snow_cm) & (pl.col("max_wind") >= p.wind_min_kmh)
        return self.result(
            ctx,
            ref,
            period,
            probability=share(members, slab),
            members=members.height,
            window_start=start,
            window_end=ski_end,
            drivers={
                "fresh_snow_cm_p50": quantile(members["fresh_snow"], 0.5, 0),
                "max_wind_kmh_p50": quantile(members["max_wind"], 0.5, 0),
                "members": members.height,
            },
        )
