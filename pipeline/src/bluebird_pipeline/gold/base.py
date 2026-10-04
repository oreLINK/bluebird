"""Gold layer contract: ``Aggregator`` classes compute one KPI from silver tables.

Live KPIs (``Aggregator``): a probability in [0, 1] for one station and one
forecast date, plus a confidence level and explanatory ``drivers``. All results
of a run are stored together in ``gold/kpis/date=<date>/kpis.parquet``.

Historical KPIs (``SeasonAggregator``, kind ``historical``): one value (cm,
hours…) per station over a closed season, computed by ``bluebird rewind`` from
the season's hourly table and stored in ``gold/rewind/{rewind_id}/kpis.parquet``.
Both kinds share the aggregator registry and the ``aggregator_*.py`` naming.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from datetime import UTC, date, datetime
from typing import Any, ClassVar, Literal

import polars as pl
from pydantic import BaseModel, ConfigDict, Field

from ..config import Kpi, KpiKind, Rewind, StationRef
from ..context import RunContext
from ..registry import Registry

Confidence = Literal["low", "medium", "high"]
DriverValue = float | int | str | None


class KpiResult(BaseModel):
    """One KPI value for one station and one forecast date."""

    kpi_id: str
    station_id: str
    massif_id: str
    forecast_date: date
    probability: float = Field(ge=0, le=1)
    confidence: Confidence
    window_start: datetime
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
    """Compute one KPI for every station of the run.

    Subclasses set a nested ``Params`` model (validated from ``kpis.yaml``),
    list the silver ``required_datasets``, implement :meth:`aggregate`, and
    register with ``@register_aggregator("id")``. Bump ``version`` whenever the
    computation changes, so gold history stays interpretable.
    """

    id: ClassVar[str]
    kind: ClassVar[KpiKind] = "live"
    version: ClassVar[str] = "1"
    Params: ClassVar[type[AggregatorParams]] = AggregatorParams
    required_datasets: ClassVar[tuple[str, ...]] = ()

    def __init__(self, kpi: Kpi) -> None:
        self.kpi = kpi
        self.params = self.Params.model_validate(kpi.params)

    @abstractmethod
    def aggregate(self, ctx: RunContext) -> list[KpiResult]:
        """Return one :class:`KpiResult` per station with enough data."""

    def result(
        self,
        ctx: RunContext,
        ref: StationRef,
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
            forecast_date=ctx.run_date,
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


# ------------------------------------------------------------- historical KPIs

SEASON_DATASET = "season_hourly"


class SeasonKpiResult(BaseModel):
    """One historical KPI value for one station over one Rewind season."""

    kpi_id: str
    station_id: str
    massif_id: str
    rewind_id: str
    value: float
    unit: str
    drivers: dict[str, DriverValue] = Field(default_factory=dict)
    aggregator: str
    aggregator_version: str


class SeasonAggregator(ABC):
    """Compute one historical KPI for every station from a season's hourly table.

    ``aggregate`` receives the ``season_hourly`` rows of the run's stations,
    already limited to the season window ``(start, end]``. Subclasses register
    with ``@register_aggregator("id")`` like live aggregators.
    """

    id: ClassVar[str]
    kind: ClassVar[KpiKind] = "historical"
    version: ClassVar[str] = "1"
    Params: ClassVar[type[AggregatorParams]] = AggregatorParams
    required_datasets: ClassVar[tuple[str, ...]] = (SEASON_DATASET,)

    def __init__(self, kpi: Kpi) -> None:
        self.kpi = kpi
        self.params = self.Params.model_validate(kpi.params)

    @abstractmethod
    def aggregate(
        self, ctx: RunContext, rewind: Rewind, hourly: pl.DataFrame
    ) -> list[SeasonKpiResult]:
        """Return one :class:`SeasonKpiResult` per station with data."""

    def result(
        self,
        rewind: Rewind,
        ref: StationRef,
        *,
        value: float,
        drivers: dict[str, DriverValue],
    ) -> SeasonKpiResult:
        """``value`` is in the aggregator's unit; it is published in ``kpi.value.unit``."""
        spec = self.kpi.value
        decimals = spec.decimals if spec else 1
        scale = spec.scale if spec else 1.0
        return SeasonKpiResult(
            kpi_id=self.kpi.id,
            station_id=ref.station.id,
            massif_id=ref.massif.id,
            rewind_id=rewind.id,
            value=round(float(value) * scale, decimals + 1),
            unit=spec.unit if spec else "",
            drivers=drivers,
            aggregator=self.id,
            aggregator_version=self.version,
        )


SEASON_GOLD_SCHEMA: dict[str, Any] = {
    "kpi_id": pl.Utf8,
    "station_id": pl.Utf8,
    "massif_id": pl.Utf8,
    "rewind_id": pl.Utf8,
    "value": pl.Float64,
    "unit": pl.Utf8,
    "drivers_json": pl.Utf8,
    "aggregator": pl.Utf8,
    "aggregator_version": pl.Utf8,
}


def season_results_to_frame(results: list[SeasonKpiResult]) -> pl.DataFrame:
    rows = [
        {
            **result.model_dump(exclude={"drivers"}),
            "drivers_json": json.dumps(result.drivers, sort_keys=True),
        }
        for result in results
    ]
    return pl.DataFrame(rows, schema=SEASON_GOLD_SCHEMA)


def frame_to_season_results(frame: pl.DataFrame) -> list[SeasonKpiResult]:
    return [
        SeasonKpiResult(
            **{k: v for k, v in row.items() if k != "drivers_json"},
            drivers=json.loads(row["drivers_json"]),
        )
        for row in frame.iter_rows(named=True)
    ]


AGGREGATORS: Registry[Aggregator | SeasonAggregator] = Registry("aggregator")
register_aggregator = AGGREGATORS.register
