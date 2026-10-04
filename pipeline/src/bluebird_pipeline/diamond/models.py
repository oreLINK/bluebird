"""Diamond payload models: the contract between the pipeline and the frontend.

These models are exported as JSON Schemas (``config/schemas/diamond-*.schema.json``)
and the frontend generates its TypeScript types from them. Any breaking change
must bump the file's ``schema_version`` and update the frontend in the same
pull request.

Versions: massif payload 2 (rankings per period), manifest 1, status 1, rewind 1.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ..report import State

MASSIF_SCHEMA_VERSION = 2
MANIFEST_SCHEMA_VERSION = 1
STATUS_SCHEMA_VERSION = 1
REWIND_SCHEMA_VERSION = 1


class DiamondModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DiamondElevation(DiamondModel):
    base: int
    mid: int
    summit: int


class DiamondStation(DiamondModel):
    id: str
    name: str
    short_name: str = Field(description="Compact name for tiles (falls back to `name`).")
    lat: float
    lon: float
    elevation: DiamondElevation
    aspects: list[str]
    website: str | None


class DiamondRankingEntry(DiamondModel):
    station_id: str
    probability: float = Field(ge=0, le=1)
    confidence: Literal["low", "medium", "high"]
    window_start: datetime = Field(description="Local time, with UTC offset.")
    window_end: datetime = Field(description="Local time, with UTC offset.")
    members: int
    drivers: dict[str, float | int | str | None]


class DiamondKpiPeriod(DiamondModel):
    """The ranking of one KPI for one period of one ski day."""

    key: str = Field(description="Stable id across runs, e.g. `evening@2026-12-14`.")
    period_id: str = Field(description="Period id from config/periods.yaml.")
    ski_day: date
    start: datetime = Field(description="Local time, with UTC offset.")
    end: datetime = Field(description="Local time, with UTC offset. Hidden afterwards.")
    generated_at: datetime = Field(
        description="When these values were computed; older than the payload = stale."
    )
    ranking: list[DiamondRankingEntry] = Field(description="Sorted by probability, descending.")


class DiamondKpi(DiamondModel):
    kpi_id: str
    aggregator_version: str
    periods: list[DiamondKpiPeriod] = Field(description="Periods not over yet, by start time.")


class DiamondSource(DiamondModel):
    id: str
    name: str
    url: str
    license: str | None


class DiamondMassifDaily(DiamondModel):
    """``diamond/{massif_id}/latest.json`` and ``diamond/{massif_id}/{date}.json``."""

    schema_version: Literal[2] = MASSIF_SCHEMA_VERSION
    massif_id: str
    forecast_date: date = Field(
        description="Ski day of the run (local date, before 06:00: the day before)."
    )
    generated_at: datetime
    timezone: str
    stations: dict[str, DiamondStation]
    kpis: dict[str, DiamondKpi]
    sources: list[DiamondSource]


class DiamondManifestEntry(DiamondModel):
    forecast_date: date
    generated_at: datetime
    latest: str = Field(description="Path of the latest payload, relative to the diamond root.")
    archive: str = Field(description="Path of the dated payload, relative to the diamond root.")


class DiamondManifest(DiamondModel):
    """``diamond/manifest.json``: latest available payload per massif."""

    schema_version: Literal[1] = MANIFEST_SCHEMA_VERSION
    generated_at: datetime
    massifs: dict[str, DiamondManifestEntry]


class DiamondStatusItem(DiamondModel):
    """State of one source (bronze) or one transformation (silver)."""

    id: str = Field(description="Source id from config/sources.yaml.")
    dataset: str | None = Field(description="Silver dataset produced (transformations only).")
    state: State
    ok: int | None = Field(description="Stations with data, when known.")
    expected: int | None


class DiamondStatusPeriod(DiamondModel):
    """State of one KPI, or one tile, for one period of one ski day."""

    key: str
    period_id: str
    ski_day: date
    start: datetime = Field(description="Local time, with UTC offset.")
    end: datetime = Field(description="Local time, with UTC offset. Over afterwards.")
    state: State
    ok: int = Field(description="Stations with a value.")
    expected: int
    updated_at: datetime | None = Field(description="When the values shown were computed.")


class DiamondStatusKpi(DiamondModel):
    id: str = Field(description="KPI id from config/kpis.yaml.")
    state: State = Field(description="Most degraded state of its periods.")
    periods: list[DiamondStatusPeriod]


class DiamondStatusTile(DiamondModel):
    tile_id: str = Field(description="Tile id from config/tiles.yaml.")
    period: DiamondStatusPeriod


class DiamondStatus(DiamondModel):
    """``diamond/status.json``: health of the last refresh, shown in the site footer."""

    schema_version: Literal[1] = STATUS_SCHEMA_VERSION
    generated_at: datetime = Field(description="Start of the refresh.")
    run_id: str
    ski_day: date
    state: State = Field(description="Most degraded state of everything below.")
    sources: list[DiamondStatusItem]
    transforms: list[DiamondStatusItem]
    kpis: list[DiamondStatusKpi]
    tiles: dict[str, list[DiamondStatusTile]] = Field(description="Per massif id.")


class DiamondRewindEntry(DiamondModel):
    station_id: str
    value: float
    drivers: dict[str, float | int | str | None]


class DiamondRewindKpi(DiamondModel):
    kpi_id: str
    aggregator_version: str
    unit: str
    ranking: list[DiamondRewindEntry] = Field(
        description="Best first: by value, descending unless the KPI `order` is asc."
    )


class DiamondRewind(DiamondModel):
    """``config/rewind/{rewind_id}/{massif_id}.json``: a closed season, ranked.

    Generated once by ``bluebird rewind`` and committed (the site bundles it at
    build time); never edited by hand.
    """

    schema_version: Literal[1] = REWIND_SCHEMA_VERSION
    rewind_id: str
    massif_id: str
    start: date = Field(description="First day of the season (local), included.")
    end: date = Field(description="Last day of the season (local), included.")
    generated_at: datetime
    timezone: str
    stations: dict[str, DiamondStation]
    kpis: dict[str, DiamondRewindKpi]
    sources: list[DiamondSource]
