"""Open-Meteo Forecast API: deterministic high-resolution models.

Used with ``meteofrance_seamless`` (AROME 1.3 km blended with ARPEGE), the best
resolution available for the Pyrenees relief. Deterministic values complement
the ensemble probabilities as explanatory drivers.

Docs: https://open-meteo.com/en/docs/meteofrance-api
"""

from __future__ import annotations

from typing import ClassVar

from ._open_meteo import OpenMeteoExtractor, OpenMeteoParams
from .base import ExtractorParams, register_extractor


class OpenMeteoForecastParams(OpenMeteoParams):
    base_url: str = "https://api.open-meteo.com/v1/forecast"


@register_extractor("open_meteo_forecast")
class ExtractorOpenMeteoForecast(OpenMeteoExtractor):
    """Hourly deterministic forecast per station and elevation band."""

    Params: ClassVar[type[ExtractorParams]] = OpenMeteoForecastParams
