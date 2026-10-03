"""KPI ``onpiste_powder_chance``: fresh snow on the pistes after grooming.

Snow that falls between the end of grooming and lifts opening stays on the
pistes untouched. Probability = share of ensemble members whose snowfall over
``(grooming_end, lifts_open]`` reaches ``threshold_cm`` at the chosen band.

``grooming_end`` and ``lifts_open`` come from the station configuration. When
``grooming_end`` is later than ``lifts_open`` (e.g. 22:00), it refers to the
previous evening.
"""

from __future__ import annotations

import logging
from typing import ClassVar

import polars as pl
from pydantic import Field

from ..config import Band
from ..context import RunContext
from ._ensemble import member_window, quantile
from .base import Aggregator, AggregatorParams, KpiResult, register_aggregator

log = logging.getLogger(__name__)


class OnpisteParams(AggregatorParams):
    band: Band = "mid"
    threshold_cm: float = Field(default=5.0, gt=0)


@register_aggregator("onpiste_powder_chance")
class AggregatorOnpistePowderChance(Aggregator):
    """P(snowfall between grooming end and lifts opening >= threshold)."""

    version: ClassVar[str] = "1"
    Params: ClassVar[type[AggregatorParams]] = OnpisteParams
    required_datasets: ClassVar[tuple[str, ...]] = ("ensemble_hourly",)
    params: OnpisteParams

    def aggregate(self, ctx: RunContext) -> list[KpiResult]:
        ensemble = ctx.silver("ensemble_hourly")
        p = self.params
        results: list[KpiResult] = []
        for ref in ctx.stations():
            day_offset = -1 if ref.grooming_end > ref.lifts_open else 0
            start = ctx.local_datetime(ref.massif, ref.grooming_end, day_offset)
            end = ctx.local_datetime(ref.massif, ref.lifts_open)
            if end <= start:
                log.warning("%s: empty grooming window for %s", self.kpi.id, ref.id)
                continue
            totals = member_window(
                ensemble,
                station_id=ref.id,
                band=p.band,
                start=start,
                end=end,
                column="snowfall_cm",
                how="sum",
            )
            if totals.is_empty():
                log.warning("%s: no complete ensemble data for %s", self.kpi.id, ref.id)
                continue
            snow = totals["value"]
            results.append(
                self.result(
                    ctx,
                    ref,
                    probability=float((snow >= p.threshold_cm).cast(pl.Float64).mean()),
                    members=len(snow),
                    window_start=start,
                    window_end=end,
                    drivers={
                        "snow_after_grooming_cm_p50": quantile(snow, 0.5),
                        "snow_after_grooming_cm_p90": quantile(snow, 0.9),
                        "window_hours": round((end - start).total_seconds() / 3600),
                        "members": len(snow),
                    },
                )
            )
        return results
