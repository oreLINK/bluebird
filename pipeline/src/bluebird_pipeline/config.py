"""Configuration models, loading and cross-file validation.

All human-edited configuration lives in the repository ``config/`` folder as
YAML. This module defines one strict pydantic model per file. Unknown keys are
rejected, so typos fail loudly instead of being silently ignored.

The same models are exported as JSON Schemas (``bluebird schemas``). Editors use
them to validate YAML, and the frontend generates its TypeScript types from them.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
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

KpiKind = Literal["live", "historical"]
"""live: a probability for today (daily run); historical: a value over a past season (Rewind)."""

HttpUrl = Annotated[str, StringConstraints(pattern=r"^https://\S+$")]
"""Absolute https:// URL."""


_PLACEHOLDER = re.compile(r"\{(\w+)\}")


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
    order: int = Field(default=100, description="Sort order in the site menu.")
    bbox: list[float] = Field(
        min_length=4, max_length=4, description="[min_lon, min_lat, max_lon, max_lat]"
    )
    skyline: list[Annotated[float, Field(ge=0, le=1)]] = Field(
        default_factory=list,
        description="Relative ridge heights (0..1), west to east, for the banner illustrations.",
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
    short_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=20,
        description="Compact name displayed in the tiles; defaults to `name`.",
    )
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


class ValueSpec(StrictModel):
    """Unit of the value of a historical KPI, as published and displayed (e.g. 4.43 m)."""

    unit: str = Field(min_length=1)
    decimals: int = Field(default=0, ge=0, le=3)
    scale: float = Field(
        default=1.0,
        gt=0,
        description=(
            "Multiplier from the aggregator's unit (cm for snow, h for durations) to `unit`, "
            "e.g. 0.01 to publish centimetres as metres."
        ),
    )
    unit_label: Localized | None = Field(
        default=None,
        description="Unit as shown on the site when it differs by language (e.g. jours / days).",
    )
    unit_label_one: Localized | None = Field(
        default=None,
        description="Singular of `unit_label` (e.g. jour / day), used where the language says so.",
    )
    max: float | None = Field(
        default=None,
        gt=0,
        description=(
            "Value (in `unit`) of a full bar in the tiles, e.g. 100 for a percentage. "
            "Default: the best value of the ranking."
        ),
    )


class Kpi(StrictModel):
    """A KPI computed by a gold-layer Aggregator."""

    id: Slug
    aggregator: Slug = Field(description="Id of a registered gold Aggregator.")
    kind: KpiKind = Field(
        default="live",
        description=(
            "live: probability for today, computed by the daily run; historical: value over "
            "a past season, computed by `bluebird rewind` (config/rewinds.yaml)."
        ),
    )
    value: ValueSpec | None = Field(
        default=None, description="Unit and decimals of the value; required for historical KPIs."
    )
    order: Literal["desc", "asc"] = Field(
        default="desc",
        description=(
            "Ranking order: desc puts the highest value first; asc the lowest "
            "(e.g. fewest white days)."
        ),
    )
    enabled: bool = True
    name: Localized
    description: Localized
    method: Localized | None = Field(
        default=None,
        description=(
            "How the KPI is computed, in plain words, shown on the back of its tiles. "
            "`{param}` placeholders are replaced by the values of `params`."
        ),
    )
    params: dict[str, Any] = Field(default_factory=dict)
    drivers: dict[str, DriverSpec] = Field(default_factory=dict)
    filters: list[Slug] = Field(
        default_factory=list,
        description="Ids of the filters (config/filters.yaml) this KPI appears under.",
    )

    @model_validator(mode="after")
    def _value_for_historical(self) -> Kpi:
        if self.kind == "historical" and self.value is None:
            raise ValueError(f"historical KPI '{self.id}' needs `value` (unit, decimals)")
        return self


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


class Filter(StrictModel):
    """A chip of the filter bar: shows the tiles of the KPIs tagged with its id."""

    id: Slug
    name: Localized
    icon: str | None = None
    all: bool = Field(
        default=False, description="Show every tile, except those of exclusive filters."
    )
    exclusive: bool = Field(
        default=False,
        description="Its tiles appear only under this filter, never under an `all` filter.",
    )
    theme: Literal["default", "rewind"] = Field(
        default="default", description="Colour of the chip (rewind: Christmas red)."
    )


class FiltersFile(StrictModel):
    """Schema of ``config/filters.yaml``: the filter bar, in display order."""

    filters: list[Filter] = Field(min_length=1)


class LayoutFile(StrictModel):
    """Schema of ``config/layout.yaml``: tile order, optionally per massif."""

    default: list[Slug]
    overrides: dict[str, list[Slug]] = Field(default_factory=dict)


# ------------------------------------------------------------------------ sources


class Attribution(StrictModel):
    """Credit displayed on the tile backs and on the "about" page (config/pages.yaml)."""

    name: str
    url: str
    license: str | None = None


class Source(StrictModel):
    """A data source: a bronze Extractor paired with a silver Transformer."""

    id: Slug
    extractor: Slug
    transformer: Slug
    enabled: bool = True
    schedule: Literal["daily", "on_demand", "reference", "season"] = Field(
        default="daily",
        description=(
            "daily: fetched every morning; on_demand: only with `bluebird run --source`; "
            "reference: slow-changing data refreshed with `bluebird reference` and "
            "committed under config/reference/; season: archive of a closed season, "
            "fetched once by `bluebird rewind` and committed under config/rewind/."
        ),
    )
    params: dict[str, Any] = Field(default_factory=dict)
    attribution: Attribution


class SourcesFile(StrictModel):
    """Schema of ``config/sources.yaml``."""

    sources: list[Source]


# ------------------------------------------------------------------------ rewinds


class Rewind(StrictModel):
    """A Rewind: the review of a closed ski season, ranked on historical KPIs."""

    id: Slug = Field(description="Season id, e.g. 2025-26; also the folder in config/rewind/.")
    name: Localized
    start: date = Field(description="First day of the season (local), included.")
    end: date = Field(description="Last day of the season (local), included.")
    massifs: list[Slug] = Field(min_length=1)
    kpis: list[Slug] = Field(min_length=1, description="Historical KPIs of this Rewind.")
    filter: Slug = Field(description="Exclusive filter (config/filters.yaml) showing its tiles.")
    enabled: bool = True

    @model_validator(mode="after")
    def _ordered(self) -> Rewind:
        if self.end <= self.start:
            raise ValueError(f"rewind '{self.id}': end must be after start")
        return self

    def window(self, tz: ZoneInfo) -> tuple[datetime, datetime]:
        """``(start, end]`` of the season as aware datetimes: local midnights."""
        start = datetime.combine(self.start, time(0), tzinfo=tz)
        end = datetime.combine(self.end + timedelta(days=1), time(0), tzinfo=tz)
        return start, end


class RewindsFile(StrictModel):
    """Schema of ``config/rewinds.yaml``."""

    rewinds: list[Rewind] = Field(default_factory=list)


# -------------------------------------------------------------------------- pages


class PageLink(StrictModel):
    """An external link listed in a page section."""

    label: Localized
    url: HttpUrl


class PageSection(StrictModel):
    """A titled section of a page: paragraphs, links and/or a built-in block."""

    id: Slug
    title: Localized
    paragraphs: list[Localized] = Field(default_factory=list)
    links: list[PageLink] = Field(default_factory=list)
    block: Literal["data_sources", "photo_credits"] | None = Field(
        default=None,
        description=(
            "Content generated by the site after the paragraphs: data_sources lists the "
            "attribution of every enabled source (config/sources.yaml); photo_credits "
            "lists every banner photo credit (web/src/assets/photos/credits.yaml)."
        ),
    )

    @model_validator(mode="after")
    def _not_empty(self) -> PageSection:
        if not (self.paragraphs or self.links or self.block):
            raise ValueError(f"section '{self.id}' needs paragraphs, links or a block")
        return self


class Page(StrictModel):
    """A full-window page opened over the site (about, legal notice…)."""

    id: Slug = Field(description="Also the URL hash that opens the page (#<id>).")
    title: Localized
    sections: list[PageSection] = Field(min_length=1)


class Footer(StrictModel):
    """Site footer: link to the source repository, then links to pages."""

    repository: HttpUrl
    pages: list[Slug] = Field(description="Ids of the pages linked from the footer, in order.")


class PagesFile(StrictModel):
    """Schema of ``config/pages.yaml``: footer and full-window pages."""

    footer: Footer
    pages: list[Page]


# ------------------------------------------------------------------------- config


@dataclass(frozen=True)
class Config:
    """The whole validated configuration."""

    root: Path
    massifs: list[Massif]
    stations: dict[str, StationsFile]
    kpis: list[Kpi]
    filters: list[Filter]
    tiles: list[Tile]
    layout: LayoutFile
    sources: list[Source]
    pages: PagesFile
    rewinds: list[Rewind]

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

    def enabled_kpis(self, kind: KpiKind | None = None) -> list[Kpi]:
        """Enabled KPIs, optionally of one kind (``live`` for the daily run)."""
        return [k for k in self.kpis if k.enabled and (kind is None or k.kind == kind)]

    def rewind(self, rewind_id: str) -> Rewind:
        for rewind in self.rewinds:
            if rewind.id == rewind_id:
                return rewind
        raise ConfigError(f"unknown rewind '{rewind_id}'")

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
        duplicates("filter", [f.id for f in self.filters])
        duplicates("source", [s.id for s in self.sources])

        for massif_id in sorted(massif_ids - self.stations.keys()):
            errors.append(f"massif '{massif_id}' has no config/stations/{massif_id}.yaml")
        for file_id in sorted(self.stations.keys() - massif_ids):
            errors.append(f"config/stations/{file_id}.yaml does not match any massif id")

        for kpi in self.kpis:
            for language, text in kpi.description.model_dump().items():
                if _PLACEHOLDER.search(text):
                    errors.append(
                        f"KPI '{kpi.id}' description ({language}) has a placeholder; "
                        "only `method` is filled with params: write the value"
                    )
            if kpi.method is None:
                continue
            for language, text in kpi.method.model_dump().items():
                for placeholder in sorted(set(_PLACEHOLDER.findall(text)) - kpi.params.keys()):
                    errors.append(
                        f"KPI '{kpi.id}' method ({language}) uses '{{{placeholder}}}', "
                        "which is not one of its params"
                    )

        filter_ids = {f.id for f in self.filters}
        for kpi in self.kpis:
            for filter_id in kpi.filters:
                if filter_id not in filter_ids:
                    errors.append(f"KPI '{kpi.id}' references unknown filter '{filter_id}'")
        used = {fid for kpi in self.kpis if kpi.enabled for fid in kpi.filters}
        for flt in self.filters:
            if not flt.all and flt.id not in used:
                errors.append(f"filter '{flt.id}' matches no enabled KPI")

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

        kpis_by_id = {k.id: k for k in self.kpis}
        filters_by_id = {f.id: f for f in self.filters}
        duplicates("rewind", [r.id for r in self.rewinds])
        for flt in self.filters:
            if flt.all and flt.exclusive:
                errors.append(f"filter '{flt.id}' cannot be both `all` and `exclusive`")
        for rewind in self.rewinds:
            for massif_id in rewind.massifs:
                if massif_id not in massif_ids:
                    errors.append(f"rewind '{rewind.id}' references unknown massif '{massif_id}'")
            for kpi_id in rewind.kpis:
                kpi = kpis_by_id.get(kpi_id)
                if kpi is None:
                    errors.append(f"rewind '{rewind.id}' references unknown KPI '{kpi_id}'")
                elif kpi.kind != "historical":
                    errors.append(f"rewind '{rewind.id}': KPI '{kpi_id}' is not historical")
            flt = filters_by_id.get(rewind.filter)
            if flt is None:
                errors.append(f"rewind '{rewind.id}' references unknown filter '{rewind.filter}'")
            elif not flt.exclusive:
                errors.append(f"rewind '{rewind.id}': filter '{rewind.filter}' must be exclusive")
        in_rewinds = {kpi_id for r in self.rewinds for kpi_id in r.kpis}
        for kpi in self.kpis:
            if kpi.kind == "historical" and kpi.id not in in_rewinds:
                errors.append(f"historical KPI '{kpi.id}' is not part of any rewind")

        page_ids = {p.id for p in self.pages.pages}
        duplicates("page", [p.id for p in self.pages.pages])
        for page in self.pages.pages:
            duplicates(f"page '{page.id}' section", [s.id for s in page.sections])
        for page_id in self.pages.footer.pages:
            if page_id not in page_ids:
                errors.append(f"footer references unknown page '{page_id}'")

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
        filters=_read_model(root / "filters.yaml", FiltersFile).filters,
        tiles=_read_model(root / "tiles.yaml", TilesFile).tiles,
        layout=_read_model(root / "layout.yaml", LayoutFile),
        sources=_read_model(root / "sources.yaml", SourcesFile).sources,
        pages=_read_model(root / "pages.yaml", PagesFile),
        rewinds=_read_model(root / "rewinds.yaml", RewindsFile).rewinds,
    )
    errors = config.reference_errors()
    if errors:
        raise ConfigError("configuration is inconsistent:\n  - " + "\n  - ".join(errors))
    return config
