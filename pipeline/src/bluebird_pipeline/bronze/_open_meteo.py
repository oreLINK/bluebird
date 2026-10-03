"""Shared logic of the Open-Meteo extractors (forecast and ensemble APIs).

Both APIs accept several locations per request (comma-separated coordinates).
We send one request per station with one location per elevation band, so the
model downscales temperature and snow to each band's altitude.
"""

from __future__ import annotations

from pydantic import Field

from ..config import Band
from ..context import RunContext
from .base import BronzeRecord, Extractor, ExtractorParams


class OpenMeteoParams(ExtractorParams):
    """Parameters common to both Open-Meteo APIs."""

    base_url: str
    models: list[str] = Field(min_length=1)
    hourly: list[str] = Field(min_length=1)
    bands: list[Band] = Field(default_factory=lambda: ["base", "mid", "summit"], min_length=1)
    past_days: int = Field(default=2, ge=0, le=7)
    forecast_days: int = Field(default=3, ge=1, le=16)


class OpenMeteoExtractor(Extractor):
    """Fetch hourly data for every station at every configured elevation band."""

    params: OpenMeteoParams

    def extract(self, ctx: RunContext) -> list[BronzeRecord]:
        records: list[BronzeRecord] = []
        bands = list(self.params.bands)
        for ref in ctx.stations():
            station = ref.station
            elevations = [station.elevation.at(band) for band in bands]
            query = {
                "latitude": ",".join(str(station.lat) for _ in bands),
                "longitude": ",".join(str(station.lon) for _ in bands),
                "elevation": ",".join(str(e) for e in elevations),
                "hourly": ",".join(self.params.hourly),
                "models": ",".join(self.params.models),
                "past_days": self.params.past_days,
                "forecast_days": self.params.forecast_days,
                "timezone": "UTC",
            }
            records.append(
                self.get_json(
                    self.params.base_url,
                    query,
                    station_id=station.id,
                    context={
                        "bands": bands,
                        "elevations": elevations,
                        "models": list(self.params.models),
                        "hourly": list(self.params.hourly),
                    },
                )
            )
        return records
