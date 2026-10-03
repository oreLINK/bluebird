"""Diamond payload models: the contract between the pipeline and the frontend.

These models are exported as JSON Schemas (``config/schemas/diamond-*.schema.json``)
and the frontend generates its TypeScript types from them. Any breaking change
must bump ``schema_version`` and update the frontend in the same pull request.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

SCHEMA_VERSION = 1


class DiamondModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DiamondElevation(DiamondModel):
    base: int
    mid: int
    summit: int


class DiamondStation(DiamondModel):
    id: str
    name: str
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


class DiamondKpi(DiamondModel):
    kpi_id: str
    aggregator_version: str
    ranking: list[DiamondRankingEntry] = Field(description="Sorted by probability, descending.")


class DiamondSource(DiamondModel):
    id: str
    name: str
    url: str
    license: str | None


class DiamondMassifDaily(DiamondModel):
    """``diamond/{massif_id}/latest.json`` and ``diamond/{massif_id}/{date}.json``."""

    schema_version: Literal[1] = SCHEMA_VERSION
    massif_id: str
    forecast_date: date
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

    schema_version: Literal[1] = SCHEMA_VERSION
    generated_at: datetime
    massifs: dict[str, DiamondManifestEntry]
