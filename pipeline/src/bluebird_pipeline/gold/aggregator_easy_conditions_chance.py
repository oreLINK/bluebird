"""KPI ``easy_conditions_chance``: an easy time slot for beginners.

Beginners need little wind, a bearable cold, enough visibility to see the
relief and no snowstorm. For each ensemble scenario at ``band``, the slot is
easy when the maximum wind is at most ``wind_max_kmh``, the minimum
temperature at least ``temp_min_c``, the snowfall below ``snowfall_max_cm``
and at most ``white_share_max_pct`` % of its hours are white (the white hour rule
of :mod:`._whiteout`). Time slots only.
"""

from __future__ import annotations

from typing import ClassVar

import polars as pl
from pydantic import Field

from ..config import Band, StationRef
from ..context import PeriodInstance, RunContext
from ._ensemble import member_table, quantile, share
from ._whiteout import WhiteoutRule, clear_sky_expr, white_hour_expr
from .base import Aggregator, AggregatorParams, KpiResult, register_aggregator


class EasyConditionsParams(AggregatorParams):
    band: Band = "mid"
    wind_max_kmh: float = Field(default=25.0, gt=0)
    temp_min_c: float = -10.0
    snowfall_max_cm: float = Field(default=2.0, gt=0)
    white_share_max_pct: float = Field(default=25.0, ge=0, le=100)


@register_aggregator("easy_conditions_chance")
class AggregatorEasyConditionsChance(Aggregator):
    """P(calm, not too cold, visible and without a snowstorm during the slot)."""

    Params: ClassVar[type[AggregatorParams]] = EasyConditionsParams
    required_datasets: ClassVar[tuple[str, ...]] = ("ensemble_hourly",)
    params: EasyConditionsParams

    def compute(self, ctx: RunContext, ref: StationRef, period: PeriodInstance) -> KpiResult | None:
        if period.period.native_window:
            return None
        p = self.params
        clear_sky = clear_sky_expr("time_utc", ref.station.lat, ref.station.lon)
        members = member_table(
            ctx.silver("ensemble_hourly"),
            station_id=ref.id,
            band=p.band,
            start=period.start,
            end=period.end,
            columns=[white_hour_expr(WhiteoutRule(), clear_sky).alias("white")],
            aggs={
                "max_wind": pl.col("wind_speed_kmh").max(),
                "min_temp": pl.col("temperature_c").min(),
                "snow": pl.col("snowfall_cm").sum(),
                "white_share": pl.col("white").mean(),
            },
            required=["wind_speed_kmh", "temperature_c", "snowfall_cm", "relative_humidity_pct"],
        )
        if members.is_empty():
            return None
        easy = (
            (pl.col("max_wind") <= p.wind_max_kmh)
            & (pl.col("min_temp") >= p.temp_min_c)
            & (pl.col("snow") < p.snowfall_max_cm)
            & (pl.col("white_share") * 100 <= p.white_share_max_pct)
        )
        return self.result(
            ctx,
            ref,
            period,
            probability=share(members, easy),
            members=members.height,
            window_start=period.start,
            window_end=period.end,
            drivers={
                "max_wind_kmh_p50": quantile(members["max_wind"], 0.5, 0),
                "min_temp_c_p50": quantile(members["min_temp"], 0.5, 1),
                "members": members.height,
            },
        )
