"""Configuration models, loading and cross-file validation.

All human-edited configuration lives in the repository ``config/`` folder as
YAML. This module defines one strict pydantic model per file. Unknown keys are
rejected, so typos fail loudly instead of being silently ignored.

The same models are exported as JSON Schemas (``bluebird schemas``). Editors use
them to validate YAML, and the frontend generates its TypeScript types from them.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import time
from pathlib import Path
from typing import Annotated, Any, Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import yaml
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    ValidationError,
    field_validator,
    model_validator,
)

from .paths import default_config_dir

# --------------------------------------------------------------------------- types

Slug = Annotated[str, StringConstraints(pattern=r"^[a-z0-9]+(?:[_-][a-z0-9]+)*$")]
"""Lower-case identifier made of letters, digits, '-' and '_'."""

LocalTime = Annotated[str, StringConstraints(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")]
"""Local wall-clock time formatted HH:MM."""

Band = Literal["base", "mid", "summit"]
"""Elevation band of a station at which weather is sampled."""

Aspect = Literal["N", "NE", "E", "SE", "S", "SW", "W", "NW"]


def parse_local_time(value: str) -> time:
    """Convert an ``HH:MM`` string into a :class:`datetime.time`."""
    hours, minutes = value.split(":")
    return time(int(hours), int(minutes))


class ConfigError(ValueError):
    """Raised when a configuration file is missing, malformed or inconsistent."""


class StrictModel(BaseModel):
    """Base model: unknown keys are errors and instances are immutable."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class Localized(StrictModel):
    """A user-facing string in every supported UI language."""

    fr: str = Field(min_length=1)
    en: str = Field(min_length=1)


# ------------------------------------------------------------------------ massifs


class Massif(StrictModel):
    """A mountain range grouping several stations."""

    id: Slug
    name: Localized
    timezone: str = "Europe/Paris"
    enabled: bool = True
    order: int = Field(default=100, description="Sort order in the massif picker.")
    bbox: list[float] = Field(
        min_length=4, max_length=4, description="[min_lon, min_lat, max_lon, max_lat]"
    )
    skyline: list[Annotated[float, Field(ge=0, le=1)]] = Field(
        default_factory=list,
        description="Relative ridge heights (0..1), west to east, for the decorative backdrop.",
    )

    @field_validator("timezone")
    @classmethod
    def _known_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(f"unknown IANA timezone '{value}'") from exc
        return value

    @property
    def tz(self) -> ZoneInfo:
        return ZoneInfo(self.timezone)


class MassifsFile(StrictModel):
    """Schema of ``config/massifs.yaml``."""

    massifs: list[Massif]


# ----------------------------------------------------------------------- stations


class Elevation(StrictModel):
    """Elevations of a ski area, in metres."""

    base: int = Field(ge=0, le=5000)
    summit: int = Field(ge=0, le=5000)
    mid: int | None = Field(default=None, description="Defaults to the base/summit average.")

    @model_validator(mode="after")
    def _ordered(self) -> Elevation:
        if self.summit <= self.base:
            raise ValueError("summit must be higher than base")
        if self.mid is not None and not self.base <= self.mid <= self.summit:
            raise ValueError("mid must be between base and summit")
        return self

    def at(self, band: Band) -> int:
        """Return the elevation of a band, computing ``mid`` when it is not set."""
        if band == "mid":
            if self.mid is not None:
                return self.mid
            return round((self.base + self.summit) / 20) * 10
        return self.base if band == "base" else self.summit


class Station(StrictModel):
    """A ski resort."""

    id: Slug
    name: str = Field(min_length=1)
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    elevation: Elevation
    aspects: list[Aspect] = Field(default_factory=list, description="Dominant slope aspects.")
    grooming_end: LocalTime | None = Field(default=None, description="Overrides the default.")
    lifts_open: LocalTime | None = Field(default=None, description="Overrides the default.")
    website: str | None = None
    enabled: bool = True


class StationDefaults(StrictModel):
    """Values applied to every station of the file unless it overrides them."""

    grooming_end: LocalTime = "02:00"
    lifts_open: LocalTime = "09:00"


class StationsFile(StrictModel):
    """Schema of ``config/stations/<massif>.yaml``."""

    defaults: StationDefaults = Field(default_factory=StationDefaults)
    stations: list[Station]


@dataclass(frozen=True)
class StationRef:
    """A station resolved against its massif and its file defaults."""

    massif: Massif
    station: Station
    grooming_end: time
    lifts_open: time

    @property
    def id(self) -> str:
        return self.station.id


# --------------------------------------------------------------------------- KPIs


class DriverSpec(StrictModel):
    """How to display one explanatory value attached to a KPI result."""

    label: Localized
    unit: str | None = None
    decimals: int = Field(default=0, ge=0, le=3)


class Kpi(StrictModel):
    """A KPI computed by a gold-layer Aggregator."""

    id: Slug
    aggregator: Slug = Field(description="Id of a registered gold Aggregator.")
    enabled: bool = True
    name: Localized
    description: Localized
    params: dict[str, Any] = Field(default_factory=dict)
    drivers: dict[str, DriverSpec] = Field(default_factory=dict)


class KpisFile(StrictModel):
    """Schema of ``config/kpis.yaml``."""

    kpis: list[Kpi]


# -------------------------------------------------------------------- tiles/layout


class Tile(StrictModel):
    """A KPI container displayed on the page."""

    id: Slug
    type: Slug = Field(description="Frontend tile component id (web/src/tiles/registry.ts).")
    kpis: list[Slug] = Field(default_factory=list)
    title: Localized | None = None
    icon: str | None = None
    options: dict[str, Any] = Field(default_factory=dict)


class TilesFile(StrictModel):
    """Schema of ``config/tiles.yaml``."""

    tiles: list[Tile]


class LayoutFile(StrictModel):
    """Schema of ``config/layout.yaml``: tile order, optionally per massif."""

    default: list[Slug]
    overrides: dict[str, list[Slug]] = Field(default_factory=dict)


# ------------------------------------------------------------------------ sources


class Attribution(StrictModel):
    """Credit displayed in the site footer."""

    name: str
    url: str
    license: str | None = None


class Source(StrictModel):
    """A data source: a bronze Extractor paired with a silver Transformer."""

    id: Slug
    extractor: Slug
    transformer: Slug
    enabled: bool = True
    schedule: Literal["daily", "on_demand", "reference"] = Field(
        default="daily",
        description=(
            "daily: fetched every morning; on_demand: only with `bluebird run --source`; "
            "reference: slow-changing data refreshed with `bluebird reference` and "
            "committed under config/reference/."
        ),
    )
    params: dict[str, Any] = Field(default_factory=dict)
    attribution: Attribution


class SourcesFile(StrictModel):
    """Schema of ``config/sources.yaml``."""

    sources: list[Source]


# ------------------------------------------------------------------------- config


@dataclass(frozen=True)
class Config:
    """The whole validated configuration."""

    root: Path
    massifs: list[Massif]
    stations: dict[str, StationsFile]
    kpis: list[Kpi]
    tiles: list[Tile]
    layout: LayoutFile
    sources: list[Source]

    # -- lookups ---------------------------------------------------------------

    def massif(self, massif_id: str) -> Massif:
        for massif in self.massifs:
            if massif.id == massif_id:
                return massif
        raise ConfigError(f"unknown massif '{massif_id}'")

    def enabled_massifs(self, only: list[str] | None = None) -> list[Massif]:
        """Enabled massifs sorted by ``order``, optionally restricted to ``only``."""
        massifs = [m for m in self.massifs if m.enabled and (not only or m.id in only)]
        return sorted(massifs, key=lambda m: (m.order, m.id))

    def station_refs(self, massif_ids: list[str] | None = None) -> list[StationRef]:
        """Enabled stations of enabled massifs, with defaults resolved."""
        refs: list[StationRef] = []
        for massif in self.enabled_massifs(massif_ids):
            stations_file = self.stations.get(massif.id)
            if stations_file is None:
                continue
            defaults = stations_file.defaults
            for station in stations_file.stations:
                if not station.enabled:
                    continue
                refs.append(
                    StationRef(
                        massif=massif,
                        station=station,
                        grooming_end=parse_local_time(
                            station.grooming_end or defaults.grooming_end
                        ),
                        lifts_open=parse_local_time(station.lifts_open or defaults.lifts_open),
                    )
                )
        return refs

    def enabled_kpis(self) -> list[Kpi]:
        return [k for k in self.kpis if k.enabled]

    def enabled_sources(
        self, schedule: str | None = None, only: list[str] | None = None
    ) -> list[Source]:
        """Enabled sources; ``only`` selects sources by id regardless of schedule."""
        if only:
            unknown = set(only) - {s.id for s in self.sources}
            if unknown:
                raise ConfigError(f"unknown source(s): {', '.join(sorted(unknown))}")
            return [s for s in self.sources if s.enabled and s.id in only]
        return [
            s for s in self.sources if s.enabled and (schedule is None or s.schedule == schedule)
        ]

    # -- cross-file checks -----------------------------------------------------

    def reference_errors(self) -> list[str]:
        """Return every inconsistency between configuration files."""
        errors: list[str] = []

        def duplicates(kind: str, ids: list[str]) -> None:
            for value, count in Counter(ids).items():
                if count > 1:
                    errors.append(f"duplicate {kind} id '{value}'")

        massif_ids = {m.id for m in self.massifs}
        kpi_ids = {k.id for k in self.kpis}
        tile_ids = {t.id for t in self.tiles}

        duplicates("massif", [m.id for m in self.massifs])
        duplicates("station", [s.id for f in self.stations.values() for s in f.stations])
        duplicates("KPI", [k.id for k in self.kpis])
        duplicates("tile", [t.id for t in self.tiles])
        duplicates("source", [s.id for s in self.sources])

        for massif_id in sorted(massif_ids - self.stations.keys()):
            errors.append(f"massif '{massif_id}' has no config/stations/{massif_id}.yaml")
        for file_id in sorted(self.stations.keys() - massif_ids):
            errors.append(f"config/stations/{file_id}.yaml does not match any massif id")

        for tile in self.tiles:
            for kpi_id in tile.kpis:
                if kpi_id not in kpi_ids:
                    errors.append(f"tile '{tile.id}' references unknown KPI '{kpi_id}'")

        layouts = {"default": self.layout.default} | {
            f"overrides.{k}": v for k, v in self.layout.overrides.items()
        }
        for name, tile_list in layouts.items():
            for tile_id in tile_list:
                if tile_id not in tile_ids:
                    errors.append(f"layout '{name}' references unknown tile '{tile_id}'")
            duplicates(f"layout '{name}' tile", tile_list)
        for massif_id in self.layout.overrides:
            if massif_id not in massif_ids:
                errors.append(f"layout override for unknown massif '{massif_id}'")

        return errors


def _read_model[M: BaseModel](path: Path, model: type[M]) -> M:
    if not path.is_file():
        raise ConfigError(f"missing configuration file {path}")
    try:
        with path.open(encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
        return model.model_validate(data)
    except yaml.YAMLError as exc:
        raise ConfigError(f"{path}: invalid YAML: {exc}") from exc
    except ValidationError as exc:
        raise ConfigError(f"{path}: {exc}") from exc


def load_config(config_dir: Path | None = None) -> Config:
    """Load and validate every configuration file.

    Raises :class:`ConfigError` on schema errors or cross-file inconsistencies.
    """
    root = Path(config_dir) if config_dir else default_config_dir()
    stations_dir = root / "stations"
    config = Config(
        root=root,
        massifs=_read_model(root / "massifs.yaml", MassifsFile).massifs,
        stations={
            path.stem: _read_model(path, StationsFile)
            for path in sorted(stations_dir.glob("*.yaml"))
        },
        kpis=_read_model(root / "kpis.yaml", KpisFile).kpis,
        tiles=_read_model(root / "tiles.yaml", TilesFile).tiles,
        layout=_read_model(root / "layout.yaml", LayoutFile),
        sources=_read_model(root / "sources.yaml", SourcesFile).sources,
    )
    errors = config.reference_errors()
    if errors:
        raise ConfigError("configuration is inconsistent:\n  - " + "\n  - ".join(errors))
    return config
