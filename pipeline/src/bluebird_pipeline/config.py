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

FilterLevel = Literal["group", "day", "slot"]
"""Built-in kinds of the filter levels after level 1: sub-category, ski day, time slot."""

MAX_FILTER_LEVELS = 4
"""Depth of the filter bar: the topic chip (level 1) plus at most three levels."""

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


class Zone(StrictModel):
    """A sub-massif (level 2 of the massif bar): a French département, or abroad a
    country or region (Andorre, Aragon, Valais…)."""

    id: Slug
    name: Localized
    country: Annotated[str, StringConstraints(pattern=r"^[A-Z]{2}$")] = Field(
        default="FR", description="ISO 3166-1 alpha-2 code of the zone's country."
    )
    code: str | None = Field(default=None, description="Département number, e.g. '65'.")


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
    zones: list[Zone] = Field(
        default_factory=list,
        description="Sub-massifs (level 2 of the massif bar); every station names one.",
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
    zone: Slug | None = Field(
        default=None, description="Sub-massif of the station (`zones` of config/massifs.yaml)."
    )
    domain: Slug | None = Field(
        default=None, description="Linked ski area it belongs to (`domains` of its file)."
    )


class StationDefaults(StrictModel):
    """Values applied to every station of the file unless it overrides them."""

    grooming_end: LocalTime = "02:00"
    lifts_open: LocalTime = "09:00"


class Domain(StrictModel):
    """A linked ski area spanning several stations (Les 3 Vallées, Portes du Soleil…),
    level 3 of the massif bar; its stations may sit in several zones or countries."""

    id: Slug
    name: str = Field(min_length=1)


class StationsFile(StrictModel):
    """Schema of ``config/stations/<massif>.yaml``."""

    defaults: StationDefaults = Field(default_factory=StationDefaults)
    domains: list[Domain] = Field(default_factory=list)
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


class DisplayLevel(StrictModel):
    """A level of a `levels` display, shown from probability `min` (e.g. Oui from 0.6)."""

    min: float = Field(ge=0, le=1)
    label: Localized


class DisplayBand(StrictModel):
    """A named band of a `value` display, for values up to `max` (none: every value above)."""

    max: float | None = None
    label: Localized


class KpiDisplay(StrictModel):
    """How a live KPI is shown on its tiles (the probability is always computed).

    percent  the probability ("82 %"), optionally with a `note` driver in small
             type (e.g. the sunset time);
    value    the median of the scenarios, from `driver`, in the KPI `value` unit
             ("4 cm", "-24 °C"); the ranking follows that value (`order`), and
             reliability comes from the spread between the two `range` drivers
             (p10, p90): high within `tolerance`, medium within twice it;
             `bands` name ranges of values (e.g. the wind chill risk);
    levels   a decision from the probability ("Oui", "Possible", "Non").
    """

    kind: Literal["percent", "value", "levels"] = "percent"
    driver: str | None = Field(default=None, description="value: driver holding the median.")
    range: list[str] | None = Field(
        default=None, min_length=2, max_length=2, description="value: p10 and p90 drivers."
    )
    tolerance: float | None = Field(
        default=None, gt=0, description="value: p90 - p10 spread of a high reliability."
    )
    bands: list[DisplayBand] = Field(default_factory=list)
    levels: list[DisplayLevel] = Field(default_factory=list)
    note: str | None = Field(default=None, description="Driver shown in small type.")

    @model_validator(mode="after")
    def _complete(self) -> KpiDisplay:
        if self.kind == "value" and not (self.driver and self.range and self.tolerance):
            raise ValueError("a `value` display needs `driver`, `range` and `tolerance`")
        if self.kind == "levels":
            mins = [level.min for level in self.levels]
            if len(mins) < 2 or mins != sorted(mins, reverse=True) or mins[-1] != 0:
                raise ValueError("`levels` need 2+ levels by decreasing `min`, the last at 0")
        if self.bands:
            maxima = [band.max for band in self.bands]
            known = [m for m in maxima[:-1] if m is not None]
            if maxima[-1] is not None or len(known) != len(maxima) - 1 or known != sorted(known):
                raise ValueError("`bands` need increasing `max`, the last one without `max`")
        return self

    @property
    def drivers(self) -> list[str]:
        """Drivers the display reads."""
        return [d for d in [self.driver, *(self.range or []), self.note] if d]


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
    display: KpiDisplay = Field(
        default_factory=KpiDisplay,
        description="Live KPIs: shown as a percent (default), a value or levels.",
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
    periods: list[Slug] = Field(
        default_factory=lambda: ["day"],
        min_length=1,
        description=(
            "Ids of the periods (config/periods.yaml) a live KPI is computed for; "
            "ignored for historical KPIs."
        ),
    )

    @model_validator(mode="after")
    def _value_for_historical(self) -> Kpi:
        if self.kind == "historical" and self.value is None:
            raise ValueError(f"historical KPI '{self.id}' needs `value` (unit, decimals)")
        if self.kind == "historical" and self.display.kind != "percent":
            raise ValueError(f"historical KPI '{self.id}' is always shown as its value")
        if self.display.kind == "value" and self.value is None:
            raise ValueError(f"KPI '{self.id}': a `value` display needs `value` (unit, decimals)")
        for driver in self.display.drivers:
            if driver not in self.drivers:
                raise ValueError(f"KPI '{self.id}': display driver '{driver}' is not in `drivers`")
        return self


class KpisFile(StrictModel):
    """Schema of ``config/kpis.yaml``."""

    kpis: list[Kpi]


# ------------------------------------------------------------------------ periods


class Period(StrictModel):
    """A time slot of the ski day a KPI is computed for (morning, evening…)."""

    id: Slug
    start: LocalTime
    end: LocalTime = Field(description="'00:00' after a later start means midnight.")
    native_window: bool = Field(
        default=False,
        description=(
            "The KPI computes over its own window (e.g. the whole ski day); "
            "`start`/`end` then only decide when the period is shown."
        ),
    )
    labels: list[Localized] = Field(
        min_length=1,
        description="Label per day offset: [today, tomorrow, …], used in tile titles.",
    )
    chip: Localized | None = Field(
        default=None,
        description="Chip of the `slot` filter level (Matin, Soir…); required for time slots.",
    )


class PeriodsFile(StrictModel):
    """Schema of ``config/periods.yaml``."""

    day_start: LocalTime = Field(
        default="06:00",
        description="Local time a ski day starts: ski day D runs from D day_start to D+1.",
    )
    horizon_days: int = Field(
        default=2, ge=1, le=7, description="Ski days published: 1 = today, 2 = + tomorrow."
    )
    days: list[Localized] = Field(
        default_factory=list,
        description="Chips of the `day` filter level, one per day of the horizon: [today, …].",
    )
    periods: list[Period] = Field(min_length=1)

    def minutes_after_day_start(self, value: str) -> int:
        """Minutes from ``day_start`` to the wall-clock ``value`` (0..1439)."""
        start = parse_local_time(self.day_start)
        moment = parse_local_time(value)
        delta = (moment.hour * 60 + moment.minute) - (start.hour * 60 + start.minute)
        return delta % 1440

    def span(self, period: Period) -> tuple[int, int]:
        """``(start, end)`` of ``period`` in minutes after ``day_start``; end in 1..1440."""
        start = self.minutes_after_day_start(period.start)
        end = self.minutes_after_day_start(period.end) or 1440
        return start, end

    def errors(self) -> list[str]:
        errors: list[str] = []
        slots: list[tuple[int, int, str]] = []
        for period in self.periods:
            start, end = self.span(period)
            if end <= start:
                errors.append(f"period '{period.id}' ends before it starts")
            if len(period.labels) < self.horizon_days:
                errors.append(
                    f"period '{period.id}' needs {self.horizon_days} labels "
                    f"(one per day of the horizon), has {len(period.labels)}"
                )
            if not period.native_window:
                slots.append((start, end, period.id))
                if period.chip is None:
                    errors.append(f"time slot '{period.id}' needs a `chip` label (filter bar)")
        if len(self.days) < self.horizon_days:
            errors.append(
                f"`days` needs {self.horizon_days} chip labels "
                f"(one per day of the horizon), has {len(self.days)}"
            )
        cursor = 0
        for start, end, period_id in sorted(slots):
            if start != cursor:
                kind = "overlaps the previous slot" if start < cursor else "leaves a gap before it"
                errors.append(f"period '{period_id}' {kind}")
            cursor = max(cursor, end)
        if slots and cursor != 1440:
            errors.append("time slots must cover the whole ski day (24 h from day_start)")
        return errors


# -------------------------------------------------------------------- tiles/layout


class Tile(StrictModel):
    """A KPI container displayed on the page."""

    id: Slug
    type: Slug = Field(description="Frontend tile component id (web/src/tiles/registry.ts).")
    kpis: list[Slug] = Field(default_factory=list)
    title: Localized | None = Field(
        default=None,
        description=(
            "Defaults to the first KPI's name. A tile of live KPIs must contain `{period}`, "
            "replaced by the period label (e.g. 'Neige {period}' -> 'Neige ce soir'); a "
            "tile of historical KPIs (Rewind) must not."
        ),
    )
    icon: str | None = None
    periods: list[Slug] | None = Field(
        default=None,
        description=(
            "Periods to show a tile of live KPIs for; defaults to every period of its KPIs."
        ),
    )
    options: dict[str, Any] = Field(default_factory=dict)


class TilesFile(StrictModel):
    """Schema of ``config/tiles.yaml``."""

    tiles: list[Tile]


class FilterGroup(StrictModel):
    """A sub-category of a level-1 filter (level `group`), e.g. Poudreuse under Glisse."""

    id: Slug
    name: Localized
    icon: str | None = None
    kpis: list[Slug] = Field(min_length=1, description="KPIs of the sub-category.")


class Filter(StrictModel):
    """A level-1 chip of the filter bar: shows the tiles of the KPIs tagged with its id."""

    id: Slug
    name: Localized
    icon: str | None = None
    theme: Literal["default", "rewind"] = Field(
        default="default", description="Colour of the chip (rewind: Christmas red)."
    )
    levels: list[FilterLevel] = Field(
        default_factory=list,
        max_length=MAX_FILTER_LEVELS - 1,
        description=(
            "Levels offered once this filter is chosen, in order: `group` (its "
            "`groups`), `day` (today, tomorrow), `slot` (morning, evening…). Live KPIs only."
        ),
    )

    groups: list[FilterGroup] = Field(
        default_factory=list,
        description="Sub-categories for the `group` level; every KPI of the filter in one.",
    )

    @field_validator("levels")
    @classmethod
    def _unique_levels(cls, value: list[str]) -> list[str]:
        if len(set(value)) != len(value):
            raise ValueError("a filter level kind can only appear once")
        return value


class FiltersFile(StrictModel):
    """Schema of ``config/filters.yaml``: the filter bar, in display order."""

    filters: list[Filter] = Field(min_length=1)


class HomeTile(StrictModel):
    """A tile of the home page (no filter selected), for one of its periods."""

    tile: Slug = Field(description="Live tile of config/tiles.yaml.")
    period: Slug = Field(description="Period shown (today's, or tomorrow's once today's is over).")


class LayoutFile(StrictModel):
    """Schema of ``config/layout.yaml``: home page and tile order, optionally per massif."""

    home: list[HomeTile] = Field(
        default_factory=list,
        description="Home page tiles in priority order: the first one is shown first.",
    )
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
            "daily: fetched by every refresh; on_demand: only with `bluebird run --source`; "
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
    filter: Slug = Field(
        description="Level-1 filter (config/filters.yaml) showing its tiles (no levels)."
    )
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
    block: (
        Literal[
            "data_sources",
            "photo_credits",
            "service_summary",
            "service_sources",
            "service_transforms",
            "service_kpis",
            "service_tiles",
        ]
        | None
    ) = Field(
        default=None,
        description=(
            "Content generated by the site after the paragraphs: data_sources lists the "
            "attribution of every enabled source (config/sources.yaml); photo_credits "
            "lists every banner photo credit (web/src/assets/photos/credits.yaml); "
            "service_* show the status of the last refresh (diamond/status.json): "
            "summary, data sources, transformations, KPIs, tiles of the current massif."
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
    periods: PeriodsFile
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

    def kpi(self, kpi_id: str) -> Kpi:
        for kpi in self.kpis:
            if kpi.id == kpi_id:
                return kpi
        raise ConfigError(f"unknown KPI '{kpi_id}'")

    def period(self, period_id: str) -> Period:
        for period in self.periods.periods:
            if period.id == period_id:
                return period
        raise ConfigError(f"unknown period '{period_id}'")

    def is_live_tile(self, tile: Tile) -> bool:
        """Whether a tile shows live KPIs (one tile per period) rather than a Rewind."""
        kinds = {k.kind for k in self.kpis if k.id in tile.kpis}
        return "live" in kinds or not kinds

    def tile_periods(self, tile: Tile) -> list[str]:
        """Period ids a tile is shown for, in ``periods.yaml`` order (none for a Rewind)."""
        if not self.is_live_tile(tile):
            return []
        wanted = set(tile.periods or [])
        if not wanted:
            for kpi_id in tile.kpis:
                kpi = next((k for k in self.kpis if k.id == kpi_id), None)
                wanted.update(kpi.periods if kpi else [])
        return [p.id for p in self.periods.periods if p.id in wanted]

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
        for massif in self.massifs:
            duplicates(f"massif '{massif.id}' zone", [z.id for z in massif.zones])
            stations_file = self.stations.get(massif.id)
            if stations_file is None:
                continue
            zone_ids = {z.id for z in massif.zones}
            domain_ids = {d.id for d in stations_file.domains}
            duplicates(f"massif '{massif.id}' domain", [d.id for d in stations_file.domains])
            for station in stations_file.stations:
                if zone_ids and station.zone not in zone_ids:
                    errors.append(
                        f"station '{station.id}' needs a zone of massif '{massif.id}' "
                        f"({', '.join(sorted(zone_ids))}), has {station.zone!r}"
                    )
                elif not zone_ids and station.zone is not None:
                    errors.append(f"station '{station.id}': massif '{massif.id}' has no zones")
                if station.domain is not None and station.domain not in domain_ids:
                    errors.append(
                        f"station '{station.id}' references unknown domain '{station.domain}'"
                    )
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
            if flt.id not in used:
                errors.append(f"filter '{flt.id}' matches no enabled KPI")
            tagged = [k for k in self.kpis if flt.id in k.filters]
            if flt.levels and any(k.kind != "live" for k in tagged):
                errors.append(f"filter '{flt.id}' has levels but shows historical KPIs")
            if ("group" in flt.levels) != bool(flt.groups):
                errors.append(f"filter '{flt.id}': the `group` level and `groups` go together")
            duplicates(f"filter '{flt.id}' group", [g.id for g in flt.groups])
            grouped = [kpi_id for g in flt.groups for kpi_id in g.kpis]
            tagged_ids = {k.id for k in tagged}
            for kpi_id in sorted(set(grouped) - tagged_ids):
                errors.append(f"filter '{flt.id}': group KPI '{kpi_id}' is not tagged with it")
            if flt.groups:
                for kpi_id in sorted(tagged_ids - set(grouped)):
                    errors.append(f"filter '{flt.id}': KPI '{kpi_id}' is in no group")
                for kpi_id, count in Counter(grouped).items():
                    if count > 1:
                        errors.append(f"filter '{flt.id}': KPI '{kpi_id}' is in several groups")

        errors.extend(f"periods.yaml: {e}" for e in self.periods.errors())
        duplicates("period", [p.id for p in self.periods.periods])
        period_ids = {p.id for p in self.periods.periods}
        for kpi in self.kpis:
            for period_id in kpi.periods:
                if period_id not in period_ids:
                    errors.append(f"KPI '{kpi.id}' references unknown period '{period_id}'")

        for tile in self.tiles:
            for kpi_id in tile.kpis:
                if kpi_id not in kpi_ids:
                    errors.append(f"tile '{tile.id}' references unknown KPI '{kpi_id}'")
            live = self.is_live_tile(tile)
            if tile.title is not None:
                for language, text in tile.title.model_dump().items():
                    if live and "{period}" not in text:
                        errors.append(
                            f"tile '{tile.id}' title ({language}) must contain '{{period}}'"
                        )
                    elif not live and "{period}" in text:
                        errors.append(
                            f"Rewind tile '{tile.id}' title ({language}) cannot use '{{period}}'"
                        )
            if not live and tile.periods:
                errors.append(f"Rewind tile '{tile.id}' cannot list periods")
            kpi_periods = {p for k in self.kpis if k.id in tile.kpis for p in k.periods}
            for period_id in tile.periods or []:
                if period_id not in kpi_periods:
                    errors.append(
                        f"tile '{tile.id}' period '{period_id}' is not computed by its KPIs"
                    )

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
        tiles_by_id = {t.id: t for t in self.tiles}
        duplicates("layout 'home' entry", [f"{h.tile}@{h.period}" for h in self.layout.home])
        for home in self.layout.home:
            tile = tiles_by_id.get(home.tile)
            if tile is None:
                errors.append(f"layout 'home' references unknown tile '{home.tile}'")
            elif not self.is_live_tile(tile):
                errors.append(f"layout 'home': Rewind tile '{tile.id}' cannot be on the home page")
            elif home.period not in self.tile_periods(tile):
                errors.append(
                    f"layout 'home': tile '{tile.id}' is not shown for period '{home.period}'"
                )

        kpis_by_id = {k.id: k for k in self.kpis}
        filters_by_id = {f.id: f for f in self.filters}
        duplicates("rewind", [r.id for r in self.rewinds])
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
            elif flt.levels:
                errors.append(f"rewind '{rewind.id}': filter '{rewind.filter}' cannot have levels")
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


class _StrictLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate keys, like the site's YAML parser.

    PyYAML keeps the last value of a repeated key silently, so a pasted line
    could drop a value from the pipeline while the site build fails.
    """

    def construct_mapping(self, node: yaml.MappingNode, deep: bool = False) -> dict[Any, Any]:
        seen: set[Any] = set()
        for key_node, _ in node.value:
            key = self.construct_object(key_node, deep=deep)
            if key in seen:
                raise yaml.constructor.ConstructorError(
                    "while constructing a mapping",
                    node.start_mark,
                    f"duplicate key {key!r}",
                    key_node.start_mark,
                )
            seen.add(key)
        return super().construct_mapping(node, deep=deep)


def _read_model[M: BaseModel](path: Path, model: type[M]) -> M:
    if not path.is_file():
        raise ConfigError(f"missing configuration file {path}")
    try:
        with path.open(encoding="utf-8") as handle:
            data = yaml.load(handle, Loader=_StrictLoader)
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
        periods=_read_model(root / "periods.yaml", PeriodsFile),
        pages=_read_model(root / "pages.yaml", PagesFile),
        rewinds=_read_model(root / "rewinds.yaml", RewindsFile).rewinds,
    )
    errors = config.reference_errors()
    if errors:
        raise ConfigError("configuration is inconsistent:\n  - " + "\n  - ".join(errors))
    return config
