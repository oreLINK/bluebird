"""Historical KPI: number of white days ("jours blancs") of the season.

On every point of ``points`` (default: along the pistes), each ski hour is
checked with the white hour rule of :mod:`._whiteout` (in the cloud, steady
snowfall or flat light). An hour is white for the station when at least
``min_point_share`` of its points are; a day is white when at least
``min_white_hours`` of its ski hours are. Value: number of white days among
the season days with complete data (rank: fewest first, KPI ``order: asc``).
Drivers: days with data and the share of white days.
"""

from __future__ import annotations

from typing import ClassVar, Literal

import polars as pl
from pydantic import Field

from ..config import Rewind
from ..context import RunContext
from ._whiteout import WhiteoutRule, clear_sky_expr, local_day_expr, ski_hours_mask, white_hour_expr
from .base import AggregatorParams, SeasonAggregator, SeasonKpiResult, register_aggregator


class SeasonWhiteDaysParams(WhiteoutRule):
    points: Literal["station", "domain"] = "domain"
    min_point_share: float = Field(default=0.5, gt=0, le=1)
    min_coverage: float = Field(default=0.9, gt=0, le=1)


@register_aggregator("season_white_days")
class AggregatorSeasonWhiteDays(SeasonAggregator):
    Params: ClassVar[type[AggregatorParams]] = SeasonWhiteDaysParams
    params: SeasonWhiteDaysParams

    def aggregate(
        self, ctx: RunContext, rewind: Rewind, hourly: pl.DataFrame
    ) -> list[SeasonKpiResult]:
        p = self.params
        season_days = (rewind.end - rewind.start).days + 1
        results: list[SeasonKpiResult] = []
        for ref in ctx.stations():
            tz = ref.massif.timezone
            rows = hourly.filter(
                (pl.col("station_id") == ref.id)
                & (pl.col("point_kind") == p.points)
                & pl.col("relative_humidity_pct").is_not_null()
                & pl.col("shortwave_wm2").is_not_null()
                & pl.col("snowfall_cm").is_not_null()
                & ski_hours_mask(p, tz)
            )
            if rows.is_empty():
                continue
            hours = (
                rows.with_columns(
                    white=white_hour_expr(
                        p, clear_sky_expr("time_utc", pl.col("lat"), pl.col("lon"))
                    ),
                    day=local_day_expr(tz),
                )
                .group_by("day", "time_utc")
                .agg(pl.col("white").mean().alias("share"))
                .with_columns(white=pl.col("share") >= p.min_point_share)
            )
            days = (
                hours.group_by("day")
                .agg(hours=pl.len(), white_hours=pl.col("white").sum())
                .filter(pl.col("hours") >= p.ski_hours)
            )
            if days.height < p.min_coverage * season_days:
                continue
            white = days.filter(pl.col("white_hours") >= p.min_white_hours).height
            results.append(
                self.result(
                    rewind,
                    ref,
                    value=white,
                    drivers={
                        "days": days.height,
                        "white_share_pct": round(100 * white / days.height),
                    },
                )
            )
        return results
