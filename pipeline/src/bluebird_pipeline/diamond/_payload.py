"""Pieces shared by the displayers: station and source descriptions."""

from __future__ import annotations

from ..config import Config, Kpi, Source, StationRef
from ..gold.base import AGGREGATORS
from ..silver.base import TRANSFORMERS
from .models import DiamondElevation, DiamondSource, DiamondStation


def station_payloads(refs: list[StationRef]) -> dict[str, DiamondStation]:
    return {
        ref.id: DiamondStation(
            id=ref.id,
            name=ref.station.name,
            short_name=ref.station.short_name or ref.station.name,
            lat=ref.station.lat,
            lon=ref.station.lon,
            elevation=DiamondElevation(
                base=ref.station.elevation.at("base"),
                mid=ref.station.elevation.at("mid"),
                summit=ref.station.elevation.at("summit"),
            ),
            aspects=list(ref.station.aspects),
            website=ref.station.website,
        )
        for ref in refs
    }


def kpi_source_ids(config: Config, kpi: Kpi) -> list[str]:
    """Enabled sources that feed ``kpi``, in ``sources.yaml`` order.

    Derived from the aggregator (``uses_source``: its silver datasets, or its
    season columns and points), so the back of a tile cites only its KPI's own
    sources and never needs a hand-kept list.
    """
    aggregator = AGGREGATORS.get(kpi.aggregator)(kpi)
    ids: list[str] = []
    for source in config.sources:
        if not source.enabled:
            continue
        transformer = TRANSFORMERS.get(source.transformer)(source)
        columns = transformer.season_columns() if source.schedule == "season" else []
        if aggregator.uses_source(source.schedule, transformer.dataset, columns):
            ids.append(source.id)
    return ids


def source_payloads(sources: list[Source]) -> list[DiamondSource]:
    return [
        DiamondSource(
            id=source.id,
            name=source.attribution.name,
            url=source.attribution.url,
            license=source.attribution.license,
        )
        for source in sources
    ]
