"""Open-Meteo Historical Forecast API: archived high-resolution forecasts of a past season.

Used by ``bluebird rewind`` (``schedule: season``) to review a closed season,
with ``meteofrance_seamless`` (AROME HD 1.5 km, archived since late 2022): the
same model as the live KPIs, and fine enough to tell neighbouring resorts and a
ski area from its surroundings apart.

Two requests per station, each covering the whole season
(``start_date``/``end_date``):

1. the station point at the elevation of ``band`` (downscaled like the live KPIs);
2. the domain and off-piste points (see ``_season_points``), without elevation,
   so Open-Meteo uses its terrain model.

Open-Meteo counts a request of more than two weeks per location as several
calls (a five-month season ≈ 11 calls per point): keep ``min_interval_s`` high.

Docs: https://open-meteo.com/en/docs/historical-forecast-api
"""

from __future__ import annotations

from datetime import timedelta
from typing import ClassVar

from pydantic import Field

from ..config import Band
from ..context import RunContext
from ._season_points import SamplePoint, station_points
from .base import BronzeRecord, Extractor, ExtractorParams, register_extractor


class OpenMeteoHistoricalParams(ExtractorParams):
    base_url: str = "https://historical-forecast-api.open-meteo.com/v1/forecast"
    models: list[str] = Field(min_length=1, max_length=1)
    hourly: list[str] = Field(min_length=1, max_length=10)
    band: Band = "mid"
    domain_points: int = Field(default=8, ge=0, le=20)
    offpiste_points: int = Field(default=8, ge=0, le=20)
    offpiste_margin_m: float = Field(default=800.0, ge=0, le=5000)


@register_extractor("open_meteo_historical")
class ExtractorOpenMeteoHistorical(Extractor):
    """Hourly archive of a season for every station point (station, domain, off-piste)."""

    Params: ClassVar[type[ExtractorParams]] = OpenMeteoHistoricalParams
    params: OpenMeteoHistoricalParams

    def extract(self, ctx: RunContext) -> list[BronzeRecord]:
        rewind = ctx.rewind
        if rewind is None:
            raise ValueError("season sources only run from `bluebird rewind`")
        # UTC days covering the local season whatever the massif timezone.
        start_date = (rewind.start - timedelta(days=1)).isoformat()
        end_date = (rewind.end + timedelta(days=1)).isoformat()
        features = ctx.reference("domain_features")
        records: list[BronzeRecord] = []
        for ref in ctx.stations():
            points = station_points(
                ref,
                features,
                band=self.params.band,
                domain_points=self.params.domain_points,
                offpiste_points=self.params.offpiste_points,
                offpiste_margin_m=self.params.offpiste_margin_m,
            )
            groups = [points[:1], points[1:]]
            for group in groups:
                if group:
                    records.append(self._fetch(ref.id, group, start_date, end_date))
        return records

    def _fetch(
        self, station_id: str, points: list[SamplePoint], start_date: str, end_date: str
    ) -> BronzeRecord:
        query: dict[str, str] = {
            "latitude": ",".join(str(p.lat) for p in points),
            "longitude": ",".join(str(p.lon) for p in points),
            "hourly": ",".join(self.params.hourly),
            "models": ",".join(self.params.models),
            "start_date": start_date,
            "end_date": end_date,
            "timezone": "UTC",
        }
        elevations = [p.elevation for p in points]
        if all(e is not None for e in elevations):
            query["elevation"] = ",".join(str(e) for e in elevations)
        return self.get_json(
            self.params.base_url,
            query,
            station_id=station_id,
            context={
                "points": [p.as_dict() for p in points],
                "models": list(self.params.models),
                "hourly": list(self.params.hourly),
            },
        )
