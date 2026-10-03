"""OpenStreetMap Overpass API: pistes and lifts around each station.

Ski-area topology changes rarely, so this source is ``on_demand``: run it with
``bluebird run --source osm_overpass`` when stations are added or once a season.

Docs: https://wiki.openstreetmap.org/wiki/Overpass_API
"""

from __future__ import annotations

from typing import ClassVar

from pydantic import Field

from ..context import RunContext
from .base import BronzeRecord, Extractor, ExtractorParams, register_extractor


class OsmOverpassParams(ExtractorParams):
    base_url: str = "https://overpass-api.de/api/interpreter"
    radius_m: int = Field(default=4000, ge=500, le=20000)
    timeout_s: int = Field(default=90, ge=10, le=300)
    min_interval_s: float = Field(default=2.0, ge=0)


QUERY_TEMPLATE = """
[out:json][timeout:{timeout}];
(
  way["piste:type"="downhill"](around:{radius},{lat},{lon});
  way["aerialway"](around:{radius},{lat},{lon});
);
out tags geom;
"""


@register_extractor("osm_overpass")
class ExtractorOsmOverpass(Extractor):
    """Downhill pistes and aerialways within ``radius_m`` of each station."""

    Params: ClassVar[type[ExtractorParams]] = OsmOverpassParams
    params: OsmOverpassParams

    def extract(self, ctx: RunContext) -> list[BronzeRecord]:
        records: list[BronzeRecord] = []
        for ref in ctx.stations():
            query = QUERY_TEMPLATE.format(
                timeout=self.params.timeout_s,
                radius=self.params.radius_m,
                lat=ref.station.lat,
                lon=ref.station.lon,
            ).strip()
            records.append(
                self.post_form(
                    self.params.base_url,
                    {"data": query},
                    station_id=ref.station.id,
                    context={"radius_m": self.params.radius_m},
                )
            )
        return records
