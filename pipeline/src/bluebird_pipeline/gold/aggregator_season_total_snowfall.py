"""Historical KPI: total snowfall of the season at the station point.

Value: sum of hourly snowfall (cm) at the station coordinates and elevation
band of the season source, over the season window. Drivers: the snowiest day
and the number of days with at least ``snow_day_cm`` of new snow.
"""

from __future__ import annotations

from typing import ClassVar

import polars as pl
from pydantic import Field

from ..config import Rewind
from ..context import RunContext
from ._season import local_days, season_hours
from .base import AggregatorParams, SeasonAggregator, SeasonKpiResult, register_aggregator


class SeasonTotalSnowfallParams(AggregatorParams):
    snow_day_cm: float = Field(default=1.0, gt=0)
    min_coverage: float = Field(
        default=0.9, gt=0, le=1, description="Share of season hours a station needs."
    )


@register_aggregator("season_total_snowfall")
class AggregatorSeasonTotalSnowfall(SeasonAggregator):
    Params: ClassVar[type[AggregatorParams]] = SeasonTotalSnowfallParams
    params: SeasonTotalSnowfallParams

    def aggregate(
        self, ctx: RunContext, rewind: Rewind, hourly: pl.DataFrame
    ) -> list[SeasonKpiResult]:
        results: list[SeasonKpiResult] = []
        for ref in ctx.stations():
            rows = hourly.filter(
                (pl.col("station_id") == ref.id)
                & (pl.col("point_kind") == "station")
                & pl.col("snowfall_cm").is_not_null()
            )
            tz = ref.massif.tz
            if rows.height < self.params.min_coverage * season_hours(rewind, tz):
                continue
            days = (
                rows.with_columns(
                    day=pl.Series(local_days(rows["time_utc"].to_list(), tz)),
                    snow=pl.col("snowfall_cm").cast(pl.Float64),
                )
                .group_by("day")
                .agg(pl.col("snow").sum())
                .sort("snow", "day", descending=[True, False])
            )
            best = days.row(0, named=True) if days.height else None
            results.append(
                self.result(
                    rewind,
                    ref,
                    value=rows["snowfall_cm"].cast(pl.Float64).sum(),
                    drivers={
                        "best_day": best["day"] if best else None,
                        "best_day_cm": round(best["snow"], 1) if best else None,
                        "snow_days": days.filter(pl.col("snow") >= self.params.snow_day_cm).height,
                    },
                )
            )
        return results
