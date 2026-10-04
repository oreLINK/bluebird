"""Shared logic of the Open-Meteo extractors (forecast and ensemble APIs).

Both APIs accept several locations per request (comma-separated coordinates).
We send **one request per source and run** with one location per station and
elevation band, so the model downscales temperature and snow to each band's
altitude. ``max_locations_per_request`` splits it into batches if a response
ever grows too large.

Open-Meteo still counts every location in its weighted quota: grouping cuts the
number of HTTP requests (and connection overhead), not the quota consumed.
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
    max_locations_per_request: int | None = Field(
        default=None, ge=1, description="Split the request in batches; default: one request."
    )


class OpenMeteoExtractor(Extractor):
    """Fetch hourly data for every station at every configured elevation band."""

    params: OpenMeteoParams

    def extract(self, ctx: RunContext) -> list[BronzeRecord]:
        locations = [
            {
                "station_id": ref.id,
                "band": band,
                "elevation": ref.station.elevation.at(band),
                "lat": ref.station.lat,
                "lon": ref.station.lon,
            }
            for ref in ctx.stations()
            for band in self.params.bands
        ]
        size = self.params.max_locations_per_request or max(1, len(locations))
        return [
            self._fetch(locations[index : index + size]) for index in range(0, len(locations), size)
        ]

    def _fetch(self, locations: list[dict]) -> BronzeRecord:
        query = {
            "latitude": ",".join(str(loc["lat"]) for loc in locations),
            "longitude": ",".join(str(loc["lon"]) for loc in locations),
            "elevation": ",".join(str(loc["elevation"]) for loc in locations),
            "hourly": ",".join(self.params.hourly),
            "models": ",".join(self.params.models),
            "past_days": self.params.past_days,
            "forecast_days": self.params.forecast_days,
            "timezone": "UTC",
        }
        return self.get_json(
            self.params.base_url,
            query,
            context={
                "locations": [
                    {k: loc[k] for k in ("station_id", "band", "elevation")} for loc in locations
                ],
                "models": list(self.params.models),
                "hourly": list(self.params.hourly),
            },
        )
