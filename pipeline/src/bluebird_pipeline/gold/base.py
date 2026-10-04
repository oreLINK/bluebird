"""Gold layer contract: ``Aggregator`` classes compute one KPI from silver tables.

Every KPI result is a probability in [0, 1] for one station and one *period*
(morning, evening, whole day… of a ski day, see ``config/periods.yaml``), plus
a confidence level and explanatory ``drivers``. Each KPI is stored in its own
file, ``gold/kpis/date=<ski day>/<kpi_id>.parquet``, so one CI job per KPI can
write it independently.

When a KPI cannot be recomputed, the rows of an earlier run are kept for the
periods that are not over yet (see :func:`read_gold`): the site then shows the
last valid value, flagged as stale, instead of nothing.
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from datetime import UTC, date, datetime, time, timedelta
from typing import Any, ClassVar, Literal

import polars as pl
from pydantic import BaseModel, ConfigDict, Field

from ..config import Kpi, StationRef
from ..context import PeriodInstance, RunContext
from ..registry import Registry
from ..storage import gold_key

log = logging.getLogger(__name__)

Confidence = Literal["low", "medium", "high"]
DriverValue = float | int | str | None


class KpiResult(BaseModel):
    """One KPI value for one station and one period of one ski day."""

    kpi_id: str
    station_id: str
    massif_id: str
    forecast_date: date = Field(description="Ski day of the period.")
    period_id: str
    period_start: datetime = Field(description="When the period starts (display window).")
    period_end: datetime = Field(description="When the period ends: hidden afterwards.")
    probability: float = Field(ge=0, le=1)
    confidence: Confidence
    window_start: datetime = Field(description="Start of the window the KPI computed over.")
    window_end: datetime
    members: int = Field(ge=0, description="Number of ensemble members used.")
    drivers: dict[str, DriverValue] = Field(default_factory=dict)
    aggregator: str
    aggregator_version: str


def confidence_level(probability: float, members: int) -> Confidence:
    """How much the ensemble members agree.

    Agreement is ``|2p - 1|``: 1 when all members agree, 0 when they split
    50/50. Fewer than 10 members is always ``low``.
    """
    if members < 10:
        return "low"
    agreement = abs(2 * probability - 1)
    if agreement >= 0.6:
        return "high"
    if agreement >= 0.25:
        return "medium"
    return "low"


class AggregatorParams(BaseModel):
    """Base class of every Aggregator ``Params`` model (unknown keys rejected)."""

    model_config = ConfigDict(extra="forbid")


class Aggregator(ABC):
    """Compute one KPI for every station and every visible period of the run.

    Subclasses set a nested ``Params`` model (validated from ``kpis.yaml``),
    list the silver ``required_datasets``, implement :meth:`compute` for one
    station and one period, and register with ``@register_aggregator("id")``.
    Bump ``version`` whenever the computation changes, so gold history stays
    interpretable.
    """

    id: ClassVar[str]
    version: ClassVar[str] = "1"
    Params: ClassVar[type[AggregatorParams]] = AggregatorParams
    required_datasets: ClassVar[tuple[str, ...]] = ()

    def __init__(self, kpi: Kpi) -> None:
        self.kpi = kpi
        self.params = self.Params.model_validate(kpi.params)

    def aggregate(self, ctx: RunContext) -> list[KpiResult]:
        """One result per station with enough data, for each period not over yet."""
        results: list[KpiResult] = []
        skipped = 0
        for massif in ctx.massifs():
            refs = [ref for ref in ctx.stations() if ref.massif.id == massif.id]
            for period in ctx.period_instances(massif, self.kpi.periods):
                for ref in refs:
                    result = self.compute(ctx, ref, period)
                    if result is None:
                        skipped += 1
                    else:
                        results.append(result)
        if skipped:
            log.warning("%s: %d station-period(s) without complete data", self.kpi.id, skipped)
        return results

    @abstractmethod
    def compute(self, ctx: RunContext, ref: StationRef, period: PeriodInstance) -> KpiResult | None:
        """The KPI for one station and one period, or ``None`` without enough data.

        Read silver tables with ``ctx.silver()`` (cached): a missing required
        dataset raises, which fails the whole KPI for this run.
        """

    @staticmethod
    def on_ski_day(
        ctx: RunContext, ref: StationRef, period: PeriodInstance, wall_clock: time, days: int = 0
    ) -> datetime:
        """Aware local datetime of ``wall_clock`` on the period's ski day (+ ``days``)."""
        return ctx.local_datetime(ref.massif, wall_clock, period.day_offset + days)

    def result(
        self,
        ctx: RunContext,
        ref: StationRef,
        period: PeriodInstance,
        *,
        probability: float,
        members: int,
        window_start: datetime,
        window_end: datetime,
        drivers: dict[str, DriverValue],
    ) -> KpiResult:
        """Build a :class:`KpiResult` with the standard fields filled in."""
        probability = min(1.0, max(0.0, float(probability)))
        return KpiResult(
            kpi_id=self.kpi.id,
            station_id=ref.station.id,
            massif_id=ref.massif.id,
            forecast_date=period.ski_day,
            period_id=period.period_id,
            period_start=period.start,
            period_end=period.end,
            probability=round(probability, 4),
            confidence=confidence_level(probability, members),
            window_start=window_start,
            window_end=window_end,
            members=members,
            drivers=drivers,
            aggregator=self.id,
            aggregator_version=self.version,
        )


# ----------------------------------------------------------------- gold storage

GOLD_SCHEMA: dict[str, Any] = {
    "kpi_id": pl.Utf8,
    "station_id": pl.Utf8,
    "massif_id": pl.Utf8,
    "forecast_date": pl.Date,
    "period_id": pl.Utf8,
    "period_start": pl.Datetime("us", "UTC"),
    "period_end": pl.Datetime("us", "UTC"),
    "probability": pl.Float64,
    "confidence": pl.Utf8,
    "window_start": pl.Datetime("us", "UTC"),
    "window_end": pl.Datetime("us", "UTC"),
    "members": pl.Int32,
    "drivers_json": pl.Utf8,
    "aggregator": pl.Utf8,
    "aggregator_version": pl.Utf8,
    "run_id": pl.Utf8,
    "generated_at": pl.Datetime("us", "UTC"),
}


def results_to_frame(results: list[KpiResult], run_id: str, generated_at: datetime) -> pl.DataFrame:
    """Serialise KPI results to the gold table (drivers as a JSON string)."""
    rows = [
        {
            **result.model_dump(exclude={"drivers"}),
            "period_start": result.period_start.astimezone(UTC),
            "period_end": result.period_end.astimezone(UTC),
            "window_start": result.window_start.astimezone(UTC),
            "window_end": result.window_end.astimezone(UTC),
            "drivers_json": json.dumps(result.drivers, sort_keys=True),
            "run_id": run_id,
            "generated_at": generated_at,
        }
        for result in results
    ]
    if not rows:
        return pl.DataFrame(schema=GOLD_SCHEMA)
    return pl.DataFrame(rows, schema=GOLD_SCHEMA)


def frame_to_results(frame: pl.DataFrame) -> list[KpiResult]:
    """Inverse of :func:`results_to_frame`."""
    return [
        KpiResult(
            **{k: v for k, v in row.items() if k not in {"drivers_json", "run_id", "generated_at"}},
            drivers=json.loads(row["drivers_json"]),
        )
        for row in frame.iter_rows(named=True)
    ]


INSTANCE = ["kpi_id", "period_id", "forecast_date"]
"""Columns identifying one period instance of one KPI in the gold table."""


def read_gold(ctx: RunContext, kpi_ids: list[str]) -> pl.DataFrame:
    """Latest gold rows of ``kpi_ids`` for the periods not over at ``ctx.generated_at``.

    Reads the files of the run's ski day and of the day before (a refresh at
    06:00 starts a new ski day, but the previous file still holds tomorrow's
    periods). For each KPI period, only the rows of the most recent run that
    computed it are kept. Files from before periods existed are ignored.
    """
    frames: list[pl.DataFrame] = []
    for day in (ctx.run_date - timedelta(days=1), ctx.run_date):
        for kpi_id in kpi_ids:
            key = gold_key(day, kpi_id)
            if not ctx.storage.exists(key):
                continue
            frame = ctx.storage.read_parquet(key)
            if set(GOLD_SCHEMA) <= set(frame.columns):
                frames.append(frame.select(list(GOLD_SCHEMA)).cast(GOLD_SCHEMA))
    if not frames:
        return pl.DataFrame(schema=GOLD_SCHEMA)
    gold = pl.concat(frames).filter(pl.col("period_end") > ctx.generated_at)
    latest = gold.group_by(INSTANCE).agg(pl.col("generated_at").max())
    return (
        gold.join(latest, on=[*INSTANCE, "generated_at"])
        .unique(subset=[*INSTANCE, "station_id"], keep="first", maintain_order=True)
        .sort([*INSTANCE, "station_id"])
    )


AGGREGATORS: Registry[Aggregator] = Registry("aggregator")
register_aggregator = AGGREGATORS.register
