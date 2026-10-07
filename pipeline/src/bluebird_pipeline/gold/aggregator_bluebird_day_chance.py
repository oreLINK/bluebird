"""KPI ``bluebird_day_chance``: probability of a "bluebird day" at a station.

A bluebird day is a clear, sunny ski day right after a snowfall: fresh snow
everywhere under a deep blue sky. For each ensemble scenario, at the
elevation band ``band``:

1. **Fresh snow**: snowfall over the ``lookback_hours`` before the ski day
   starts (``ski_start``, local) is at least ``threshold_cm``.
2. **Sunny ski day**: at least ``min_sunny_hours`` of the ski hours
   (``ski_start``..``ski_end``) are sunny. An hour is sunny when the total
   cloud cover is at most ``cloud_max_pct`` and, when the sun is high enough
   for it to mean anything, the global radiation reaches
   ``clear_sky_index_min`` times the clear-sky radiation of that hour (the
   models' sunshine duration counts sun in steady snowfall, see CONTEXT.md).

The probability is the share of scenarios with both. Like the white day, it
only makes sense for the whole-day period (``day``, today and tomorrow).
"""

from __future__ import annotations

from datetime import UTC, timedelta
from typing import ClassVar

import polars as pl
from pydantic import Field, model_validator

from ..config import Band, StationRef
from ..context import PeriodInstance, RunContext
from ._ensemble import member_window, quantile
from ._whiteout import SkiHours, clear_sky_expr, sunny_hour_expr
from .base import Aggregator, AggregatorParams, KpiResult, register_aggregator


class BluebirdDayParams(SkiHours):
    band: Band = "mid"
    lookback_hours: int = Field(default=36, ge=6, le=96)
    threshold_cm: float = Field(default=15.0, gt=0)
    cloud_max_pct: float = Field(default=30.0, ge=0, le=100)
    clear_sky_index_min: float = Field(default=0.6, gt=0, le=1)
    min_sunny_hours: int = Field(default=6, ge=1, le=24)

    @model_validator(mode="after")
    def _sunny_hours(self) -> BluebirdDayParams:
        if self.min_sunny_hours > self.ski_hours:
            raise ValueError("min_sunny_hours exceeds the ski hours")
        return self


@register_aggregator("bluebird_day_chance")
class AggregatorBluebirdDayChance(Aggregator):
    """P(fresh snow before the ski day and a sunny ski day)."""

    version: ClassVar[str] = "1"
    Params: ClassVar[type[AggregatorParams]] = BluebirdDayParams
    required_datasets: ClassVar[tuple[str, ...]] = ("ensemble_hourly",)
    params: BluebirdDayParams

    def compute(self, ctx: RunContext, ref: StationRef, period: PeriodInstance) -> KpiResult | None:
        if not period.period.native_window:
            return None
        ensemble = ctx.silver("ensemble_hourly")
        p = self.params
        start, end = p.ski_window(period.ski_day, ref.massif.tz)
        snow = member_window(
            ensemble,
            station_id=ref.id,
            band=p.band,
            start=start - timedelta(hours=p.lookback_hours),
            end=start,
            column="snowfall_cm",
            how="sum",
            alias="new_snow",
        )
        sky = (
            ensemble.filter(
                (pl.col("station_id") == ref.id)
                & (pl.col("band") == p.band)
                & (pl.col("time_utc") > start.astimezone(UTC))
                & (pl.col("time_utc") <= end.astimezone(UTC))
            )
            .with_columns(
                sunny=sunny_hour_expr(
                    p.cloud_max_pct,
                    p.clear_sky_index_min,
                    clear_sky_expr("time_utc", ref.station.lat, ref.station.lon),
                )
            )
            .group_by("model", "member")
            .agg(
                sunny_hours=pl.col("sunny").fill_null(False).sum(),
                # Hours with the values the rule needs (a partial download never counts).
                hours=pl.col("sunny").is_not_null().sum(),
            )
            .filter(pl.col("hours") >= p.ski_hours)
        )
        members = snow.join(sky, on=["model", "member"], how="inner")
        if members.is_empty():
            return None
        bluebird = (members["new_snow"] >= p.threshold_cm) & (
            members["sunny_hours"] >= p.min_sunny_hours
        )
        return self.result(
            ctx,
            ref,
            period,
            probability=float(bluebird.mean()),  # type: ignore[arg-type]
            members=members.height,
            window_start=start - timedelta(hours=p.lookback_hours),
            window_end=end,
            drivers={
                "new_snow_cm_p50": quantile(members["new_snow"], 0.5, 0),
                "sunny_hours_p50": quantile(members["sunny_hours"].cast(pl.Float64), 0.5, 0),
                "members": members.height,
            },
        )
