"""Historical KPI: longest continuous snowfall of the season, in hours.

At the station point, an hour is snowy when at least ``min_rate_cm_h`` of snow
falls. Consecutive snowy hours form an episode; up to ``max_gap_hours`` dry
hours inside it do not break it. Value: hours from the start of the first
snowy hour to the end of the last. Drivers: start, end (local) and the snow
that fell during the episode.
"""

from __future__ import annotations

from typing import ClassVar

import polars as pl
from pydantic import Field

from ..config import Rewind
from ..context import RunContext
from ._season import longest_episode, season_hours
from .base import AggregatorParams, SeasonAggregator, SeasonKpiResult, register_aggregator


class SeasonLongestSnowfallParams(AggregatorParams):
    min_rate_cm_h: float = Field(default=0.1, gt=0)
    max_gap_hours: int = Field(default=1, ge=0, le=6)
    min_coverage: float = Field(default=0.9, gt=0, le=1)


@register_aggregator("season_longest_snowfall")
class AggregatorSeasonLongestSnowfall(SeasonAggregator):
    Params: ClassVar[type[AggregatorParams]] = SeasonLongestSnowfallParams
    params: SeasonLongestSnowfallParams

    def aggregate(
        self, ctx: RunContext, rewind: Rewind, hourly: pl.DataFrame
    ) -> list[SeasonKpiResult]:
        results: list[SeasonKpiResult] = []
        for ref in ctx.stations():
            rows = hourly.filter(
                (pl.col("station_id") == ref.id)
                & (pl.col("point_kind") == "station")
                & pl.col("snowfall_cm").is_not_null()
            ).sort("time_utc")
            tz = ref.massif.tz
            if rows.height < self.params.min_coverage * season_hours(rewind, tz):
                continue
            episode = longest_episode(
                rows["time_utc"].to_list(),
                rows["snowfall_cm"].cast(pl.Float64).to_list(),
                min_rate_cm_h=self.params.min_rate_cm_h,
                max_gap_hours=self.params.max_gap_hours,
            )
            if episode is None:
                results.append(self.result(rewind, ref, value=0, drivers={}))
                continue
            results.append(
                self.result(
                    rewind,
                    ref,
                    value=episode.hours,
                    drivers={
                        "start": episode.start.astimezone(tz).isoformat(),
                        "end": episode.end.astimezone(tz).isoformat(),
                        "snow_cm": episode.snow_cm,
                    },
                )
            )
        return results
