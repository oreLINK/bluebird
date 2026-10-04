"""Historical KPI: share of the season's days with a deep snow cover.

For each local day, Bluebird averages the snow depth over the points of
``points`` (default: along the pistes) and over the day's hours. A day counts
when that average exceeds ``threshold_cm`` (70 cm: an ideal cover, absorbing
the bumps of the terrain). Value: share of the season days with data (0..1;
published as a percentage with ``value.scale: 100``). Drivers: number of such
days, days with data, and the season's deepest daily average.
"""

from __future__ import annotations

from typing import ClassVar, Literal

import polars as pl
from pydantic import Field

from ..config import Rewind
from ..context import RunContext
from ._season import local_days, season_hours
from .base import AggregatorParams, SeasonAggregator, SeasonKpiResult, register_aggregator


class SeasonSnowDepthDaysParams(AggregatorParams):
    points: Literal["station", "domain", "offpiste"] = "domain"
    threshold_cm: float = Field(default=70.0, gt=0)
    min_coverage: float = Field(default=0.9, gt=0, le=1)


@register_aggregator("season_snow_depth_days")
class AggregatorSeasonSnowDepthDays(SeasonAggregator):
    Params: ClassVar[type[AggregatorParams]] = SeasonSnowDepthDaysParams
    params: SeasonSnowDepthDaysParams

    def aggregate(
        self, ctx: RunContext, rewind: Rewind, hourly: pl.DataFrame
    ) -> list[SeasonKpiResult]:
        p = self.params
        results: list[SeasonKpiResult] = []
        for ref in ctx.stations():
            tz = ref.massif.tz
            rows = hourly.filter(
                (pl.col("station_id") == ref.id)
                & (pl.col("point_kind") == p.points)
                & pl.col("snow_depth_m").is_not_null()
            )
            if rows.is_empty():
                continue
            # Hours with data for every point of the area: the area mean per hour.
            per_hour = rows.group_by("time_utc").agg(pl.col("snow_depth_m").cast(pl.Float64).mean())
            if per_hour.height < p.min_coverage * season_hours(rewind, tz):
                continue
            days = (
                per_hour.with_columns(day=pl.Series(local_days(per_hour["time_utc"].to_list(), tz)))
                .group_by("day")
                .agg(depth_cm=pl.col("snow_depth_m").mean() * 100)
            )
            deep = days.filter(pl.col("depth_cm") > p.threshold_cm).height
            results.append(
                self.result(
                    rewind,
                    ref,
                    value=deep / days.height,
                    drivers={
                        "deep_days": deep,
                        "days": days.height,
                        "max_depth_cm": round(float(days["depth_cm"].max()), 0),  # type: ignore[arg-type]
                    },
                )
            )
        return results
