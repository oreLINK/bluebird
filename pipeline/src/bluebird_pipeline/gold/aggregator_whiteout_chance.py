"""KPI ``whiteout_chance``: probability of a white day ("jour blanc") at a station.

For each ensemble scenario, the ski hours (``ski_start``..``ski_end`` local)
of the day ``run_date + day_offset`` are checked hour by hour with the white
hour rule of :mod:`._whiteout` (in the cloud, steady snowfall or flat light),
at the elevation band ``band``. A scenario gives a white day when at least
``min_white_hours`` hours are white; the probability is the share of such
scenarios. ``day_offset: 0`` is today, ``1`` tomorrow.

The ICON ensemble has no low cloud cover: its scenarios use the total cloud
cover instead (slightly looser "in the cloud" test).
"""

from __future__ import annotations

import logging
from datetime import UTC, timedelta
from typing import ClassVar

import polars as pl
from pydantic import Field

from ..config import Band
from ..context import RunContext
from ._ensemble import quantile
from ._whiteout import WhiteoutRule, clear_sky_expr, white_hour_expr
from .base import Aggregator, AggregatorParams, KpiResult, register_aggregator

log = logging.getLogger(__name__)


class WhiteoutChanceParams(WhiteoutRule):
    band: Band = "mid"
    day_offset: int = Field(default=0, ge=0, le=1, description="0: today, 1: tomorrow.")


@register_aggregator("whiteout_chance")
class AggregatorWhiteoutChance(Aggregator):
    """P(white day) over the ski hours of today or tomorrow."""

    version: ClassVar[str] = "1"
    Params: ClassVar[type[AggregatorParams]] = WhiteoutChanceParams
    required_datasets: ClassVar[tuple[str, ...]] = ("ensemble_hourly",)
    params: WhiteoutChanceParams

    def aggregate(self, ctx: RunContext) -> list[KpiResult]:
        ensemble = ctx.silver("ensemble_hourly")
        p = self.params
        day = ctx.run_date + timedelta(days=p.day_offset)
        results: list[KpiResult] = []
        for ref in ctx.stations():
            start, end = p.ski_window(day, ref.massif.tz)
            rows = ensemble.filter(
                (pl.col("station_id") == ref.id)
                & (pl.col("band") == p.band)
                & (pl.col("time_utc") > start.astimezone(UTC))
                & (pl.col("time_utc") <= end.astimezone(UTC))
            ).with_columns(
                white=white_hour_expr(
                    p, clear_sky_expr("time_utc", ref.station.lat, ref.station.lon)
                )
            )
            members = (
                rows.group_by("model", "member")
                .agg(
                    white_hours=pl.col("white").sum(),
                    # Hours with the values the rule needs (a partial download never counts).
                    hours=(
                        pl.col("relative_humidity_pct").is_not_null()
                        & pl.col("shortwave_wm2").is_not_null()
                        & pl.col("snowfall_cm").is_not_null()
                    ).sum(),
                )
                .filter(pl.col("hours") >= p.ski_hours)
            )
            if members.is_empty():
                log.warning("%s: no complete ensemble data for %s", self.kpi.id, ref.id)
                continue
            white_days = members["white_hours"] >= p.min_white_hours
            results.append(
                self.result(
                    ctx,
                    ref,
                    probability=float(white_days.mean()),  # type: ignore[arg-type]
                    members=members.height,
                    window_start=start,
                    window_end=end,
                    drivers={
                        "white_hours_p50": quantile(members["white_hours"].cast(pl.Float64), 0.5),
                        "members": members.height,
                    },
                )
            )
        return results
