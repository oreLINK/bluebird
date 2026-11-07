"""KPI ``avalanche_risk``: the avalanche danger level of the Météo-France bulletin.

Not a forecast of Bluebird: the level (1 to 5, European scale) is relayed as
is from the bulletin of the station's avalanche massif (``avalanche_massif``
in the stations file) valid on the period's ski day, at the station's summit
elevation (``level_high`` at or above the bulletin's altitude limit,
``level_low`` below it). The KPI is ``certified`` and shown as a ``scale``.

The probability is the level brought to 0..1, ``(level - 1) / 4``, so the
ranking puts the highest danger first. There are no scenarios: reliability
comes from the age of the bulletin, ``high`` up to ``fresh_hours`` after it was
issued, then ``medium`` at best. Only the whole-day period (``day``): today,
and tomorrow, first from the day-after trend of today's bulletin (``trend``
rows, ``medium`` reliability), then from the afternoon bulletin, which always
wins over a trend.

Out of season there is no bulletin at all: no result, which the runner
reports as normal (``empty_ok``), not as a failure.
"""

from __future__ import annotations

from typing import ClassVar

import polars as pl
from pydantic import Field

from ..config import StationRef
from ..context import PeriodInstance, RunContext
from ..silver._avalanche import AVALANCHE_DATASET
from .base import Aggregator, AggregatorParams, KpiResult, register_aggregator


class AvalancheRiskParams(AggregatorParams):
    fresh_hours: float = Field(
        default=24, gt=0, description="Bulletin age up to which reliability is high."
    )


def level_at(summit_m: int, low: int, high: int, limit_m: int | None) -> int:
    """Danger level at the summit elevation: above the altitude limit, ``high``."""
    if limit_m is None or summit_m >= limit_m:
        return high
    return low


@register_aggregator("avalanche_risk")
class AggregatorAvalancheRisk(Aggregator):
    """Danger level of the station's avalanche massif, from the official bulletin."""

    Params: ClassVar[type[AggregatorParams]] = AvalancheRiskParams
    empty_ok: ClassVar[bool] = True
    required_datasets: ClassVar[tuple[str, ...]] = (AVALANCHE_DATASET,)
    params: AvalancheRiskParams

    def compute(self, ctx: RunContext, ref: StationRef, period: PeriodInstance) -> KpiResult | None:
        number = ref.station.avalanche_massif
        if not period.period.native_window or number is None:
            return None
        bulletins = ctx.silver(AVALANCHE_DATASET).filter(
            (pl.col("massif_number") == number) & (pl.col("valid_date") == period.ski_day)
        )
        if bulletins.is_empty():
            return None
        # A bulletin beats the trend of an earlier one; then the latest wins.
        bulletin = bulletins.sort(["trend", "issued_at"], descending=[False, True]).row(
            0, named=True
        )
        summit = ref.station.elevation.summit
        level = level_at(
            summit, bulletin["level_low"], bulletin["level_high"], bulletin["altitude_limit_m"]
        )
        issued_at = bulletin["issued_at"]
        age_h = (ctx.generated_at - issued_at).total_seconds() / 3600
        return self.result(
            ctx,
            ref,
            period,
            probability=(level - 1) / 4,
            members=0,
            window_start=period.start,
            window_end=period.end,
            confidence="high"
            if age_h <= self.params.fresh_hours and not bulletin["trend"]
            else "medium",
            drivers={
                "level": level,
                "level_low": bulletin["level_low"],
                "level_high": bulletin["level_high"],
                "altitude_limit_m": bulletin["altitude_limit_m"],
                "summit_m": summit,
                "massif": bulletin["massif_name"],
                "issued_at": issued_at.isoformat(),
            },
        )
