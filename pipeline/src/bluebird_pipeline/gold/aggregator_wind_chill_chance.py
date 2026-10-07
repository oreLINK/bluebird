"""KPI ``wind_chill_chance``: biting cold in the wind during a time slot.

For each ensemble scenario at ``band`` (the summit, where the lifts arrive),
the felt temperature (wind chill index, :mod:`._conditions`) is computed hour
by hour; the slot is biting when its minimum reaches ``chill_max_c`` or less
(frostbite of exposed skin within about half an hour from -27 °C).
Time slots only.
"""

from __future__ import annotations

from typing import ClassVar

import polars as pl

from ..config import Band, StationRef
from ..context import PeriodInstance, RunContext
from ._conditions import wind_chill_expr
from ._ensemble import member_table, quantile, share
from .base import Aggregator, AggregatorParams, KpiResult, register_aggregator


class WindChillParams(AggregatorParams):
    band: Band = "summit"
    chill_max_c: float = -20.0


@register_aggregator("wind_chill_chance")
class AggregatorWindChillChance(Aggregator):
    """P(minimum wind chill of the slot <= ``chill_max_c``)."""

    Params: ClassVar[type[AggregatorParams]] = WindChillParams
    required_datasets: ClassVar[tuple[str, ...]] = ("ensemble_hourly",)
    params: WindChillParams

    def compute(self, ctx: RunContext, ref: StationRef, period: PeriodInstance) -> KpiResult | None:
        if period.period.native_window:
            return None
        p = self.params
        members = member_table(
            ctx.silver("ensemble_hourly"),
            station_id=ref.id,
            band=p.band,
            start=period.start,
            end=period.end,
            columns=[wind_chill_expr().alias("chill")],
            aggs={"min_chill": pl.col("chill").min()},
            required=["temperature_c", "wind_speed_kmh"],
        )
        if members.is_empty():
            return None
        return self.result(
            ctx,
            ref,
            period,
            probability=share(members, pl.col("min_chill") <= p.chill_max_c),
            members=members.height,
            window_start=period.start,
            window_end=period.end,
            drivers={
                "wind_chill_c_p50": quantile(members["min_chill"], 0.5, 0),
                "wind_chill_c_p10": quantile(members["min_chill"], 0.1, 0),
                "wind_chill_c_p90": quantile(members["min_chill"], 0.9, 0),
                "members": members.height,
            },
        )
