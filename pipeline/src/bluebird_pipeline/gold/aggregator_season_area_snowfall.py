"""Historical KPI: average season snowfall over an area around the station.

``points: domain`` averages the season totals of the points spread along the
station's pistes (the ski area); ``points: offpiste`` those of the points on a
ring around it. Each point needs ``min_coverage`` of the season hours. Drivers:
number of points, lowest and highest point total.
"""

from __future__ import annotations

from typing import ClassVar, Literal

import polars as pl
from pydantic import Field

from ..config import Rewind
from ..context import RunContext
from ._season import point_totals, season_hours
from .base import AggregatorParams, SeasonAggregator, SeasonKpiResult, register_aggregator


class SeasonAreaSnowfallParams(AggregatorParams):
    points: Literal["domain", "offpiste"]
    min_coverage: float = Field(default=0.9, gt=0, le=1)


@register_aggregator("season_area_snowfall")
class AggregatorSeasonAreaSnowfall(SeasonAggregator):
    Params: ClassVar[type[AggregatorParams]] = SeasonAreaSnowfallParams
    params: SeasonAreaSnowfallParams

    def aggregate(
        self, ctx: RunContext, rewind: Rewind, hourly: pl.DataFrame
    ) -> list[SeasonKpiResult]:
        results: list[SeasonKpiResult] = []
        for ref in ctx.stations():
            min_hours = round(self.params.min_coverage * season_hours(rewind, ref.massif.tz))
            totals = point_totals(
                hourly.filter(pl.col("station_id") == ref.id), self.params.points, min_hours
            )
            if totals.is_empty():
                continue
            snow = totals["snowfall_cm"]
            results.append(
                self.result(
                    rewind,
                    ref,
                    value=float(snow.mean()),  # type: ignore[arg-type]
                    drivers={
                        "points": totals.height,
                        "min_cm": round(float(snow.min()), 1),  # type: ignore[arg-type]
                        "max_cm": round(float(snow.max()), 1),  # type: ignore[arg-type]
                    },
                )
            )
        return results
