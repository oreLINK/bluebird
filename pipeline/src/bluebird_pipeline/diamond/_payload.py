"""Pieces shared by the displayers: station and source descriptions."""

from __future__ import annotations

from ..config import Source, StationRef
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
