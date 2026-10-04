"""KPI ``whiteout_chance``: probability of a white day ("jour blanc") at a station.

For each ensemble scenario, the ski hours (``ski_start``..``ski_end`` local)
of the period's ski day are checked hour by hour with the white hour rule of
:mod:`._whiteout` (in the cloud, steady snowfall or flat light), at the
elevation band ``band``. A scenario gives a white day when at least
``min_white_hours`` hours are white; the probability is the share of such
scenarios. A white *day* only makes sense for the whole-day period (``day`` in
``config/periods.yaml``, today and tomorrow): time slots give no result.

The ICON ensemble has no low cloud cover: its scenarios use the total cloud
cover instead (slightly looser "in the cloud" test).
"""

from __future__ import annotations

from datetime import UTC
from typing import ClassVar

import polars as pl

from ..config import Band, StationRef
from ..context import PeriodInstance, RunContext
from ._ensemble import quantile
from ._whiteout import WhiteoutRule, clear_sky_expr, white_hour_expr
from .base import Aggregator, AggregatorParams, KpiResult, register_aggregator


class WhiteoutChanceParams(WhiteoutRule):
    band: Band = "mid"


@register_aggregator("whiteout_chance")
class AggregatorWhiteoutChance(Aggregator):
    """P(white day) over the ski hours of the period's ski day."""

    version: ClassVar[str] = "2"
    Params: ClassVar[type[AggregatorParams]] = WhiteoutChanceParams
    required_datasets: ClassVar[tuple[str, ...]] = ("ensemble_hourly",)
    params: WhiteoutChanceParams

    def compute(self, ctx: RunContext, ref: StationRef, period: PeriodInstance) -> KpiResult | None:
        if not period.period.native_window:
            return None
        ensemble = ctx.silver("ensemble_hourly")
        p = self.params
        start, end = p.ski_window(period.ski_day, ref.massif.tz)
        rows = ensemble.filter(
            (pl.col("station_id") == ref.id)
            & (pl.col("band") == p.band)
            & (pl.col("time_utc") > start.astimezone(UTC))
            & (pl.col("time_utc") <= end.astimezone(UTC))
        ).with_columns(
            white=white_hour_expr(p, clear_sky_expr("time_utc", ref.station.lat, ref.station.lon))
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
            return None
        white_days = members["white_hours"] >= p.min_white_hours
        return self.result(
            ctx,
            ref,
            period,
            probability=float(white_days.mean()),  # type: ignore[arg-type]
            members=members.height,
            window_start=start,
            window_end=end,
            drivers={
                "white_hours_p50": quantile(members["white_hours"].cast(pl.Float64), 0.5),
                "members": members.height,
            },
        )
