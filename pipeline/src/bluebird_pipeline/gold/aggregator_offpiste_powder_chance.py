"""KPI ``offpiste_powder_chance``: fresh, unspoilt powder off-piste at opening time.

For each ensemble member, at the summit band, looking back from lifts opening:

1. ``new_snow``: snowfall over the last ``lookback_hours`` (default 36 h).
   The member scores 0 unless ``new_snow >= threshold_cm``.
2. Wind factor: wind transports and packs snow into slabs. Max wind over the
   last ``wind_lookback_hours`` maps linearly from 1 (<= ``wind_ok_kmh``) down
   to ``wind_floor`` (>= ``wind_bad_kmh``).
3. Thaw factor: if the max temperature over the last ``thaw_lookback_hours``
   exceeds ``thaw_temp_c``, snow turns heavy or crusty: score x ``thaw_factor``.

Probability = mean member score.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import ClassVar

import polars as pl
from pydantic import Field, model_validator

from ..config import Band
from ..context import RunContext
from ._ensemble import Reduction, member_window, quantile
from .base import Aggregator, AggregatorParams, KpiResult, register_aggregator

log = logging.getLogger(__name__)


class OffpisteParams(AggregatorParams):
    band: Band = "summit"
    lookback_hours: int = Field(default=36, ge=6, le=96)
    threshold_cm: float = Field(default=15.0, gt=0)
    wind_lookback_hours: int = Field(default=12, ge=1, le=48)
    wind_ok_kmh: float = Field(default=25.0, ge=0)
    wind_bad_kmh: float = Field(default=60.0, gt=0)
    wind_floor: float = Field(default=0.3, ge=0, le=1)
    thaw_lookback_hours: int = Field(default=12, ge=1, le=48)
    thaw_temp_c: float = 0.5
    thaw_factor: float = Field(default=0.3, ge=0, le=1)

    @model_validator(mode="after")
    def _wind_order(self) -> OffpisteParams:
        if self.wind_bad_kmh <= self.wind_ok_kmh:
            raise ValueError("wind_bad_kmh must be greater than wind_ok_kmh")
        return self


@register_aggregator("offpiste_powder_chance")
class AggregatorOffpistePowderChance(Aggregator):
    """Mean over members of: enough new snow x wind factor x thaw factor."""

    version: ClassVar[str] = "1"
    Params: ClassVar[type[AggregatorParams]] = OffpisteParams
    required_datasets: ClassVar[tuple[str, ...]] = ("ensemble_hourly",)
    params: OffpisteParams

    def _lookback(
        self,
        ensemble: pl.DataFrame,
        station_id: str,
        end: datetime,
        hours: int,
        column: str,
        how: Reduction,
        alias: str,
    ) -> pl.DataFrame:
        end_utc = end.astimezone(UTC)
        return member_window(
            ensemble,
            station_id=station_id,
            band=self.params.band,
            start=end_utc - timedelta(hours=hours),
            end=end_utc,
            column=column,
            how=how,
            alias=alias,
        )

    def aggregate(self, ctx: RunContext) -> list[KpiResult]:
        ensemble = ctx.silver("ensemble_hourly")
        p = self.params
        results: list[KpiResult] = []
        for ref in ctx.stations():
            opening = ctx.local_datetime(ref.massif, ref.lifts_open)
            snow = self._lookback(
                ensemble, ref.id, opening, p.lookback_hours, "snowfall_cm", "sum", "new_snow"
            )
            if snow.is_empty():
                log.warning("%s: no complete ensemble data for %s", self.kpi.id, ref.id)
                continue
            wind = self._lookback(
                ensemble,
                ref.id,
                opening,
                p.wind_lookback_hours,
                "wind_speed_kmh",
                "max",
                "max_wind",
            )
            temp = self._lookback(
                ensemble, ref.id, opening, p.thaw_lookback_hours, "temperature_c", "max", "max_temp"
            )
            members = (
                snow.join(wind, on=["model", "member"], how="left")
                .join(temp, on=["model", "member"], how="left")
                .with_columns(
                    wind_factor=(
                        1 - (pl.col("max_wind") - p.wind_ok_kmh) / (p.wind_bad_kmh - p.wind_ok_kmh)
                    )
                    .clip(0, 1)
                    .mul(1 - p.wind_floor)
                    .add(p.wind_floor)
                    .fill_null(1.0),
                    thaw=pl.when(pl.col("max_temp") > p.thaw_temp_c)
                    .then(p.thaw_factor)
                    .otherwise(1.0),
                )
                .with_columns(
                    score=(pl.col("new_snow") >= p.threshold_cm).cast(pl.Float64)
                    * pl.col("wind_factor")
                    * pl.col("thaw")
                )
            )
            results.append(
                self.result(
                    ctx,
                    ref,
                    probability=float(members["score"].mean()),
                    members=members.height,
                    window_start=opening - timedelta(hours=p.lookback_hours),
                    window_end=opening,
                    drivers={
                        "new_snow_cm_p50": quantile(members["new_snow"], 0.5, 0),
                        "max_wind_kmh_p50": quantile(members["max_wind"].drop_nulls(), 0.5, 0),
                        "max_temp_c_p50": quantile(members["max_temp"].drop_nulls(), 0.5, 1),
                        "members": members.height,
                    },
                )
            )
        return results
