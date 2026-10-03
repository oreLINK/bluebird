"""Open-Meteo Ensemble API: every member of global ensemble forecasts.

Ensembles run the same model many times with perturbed initial conditions.
The share of members exceeding a threshold is a calibrated-ish probability,
which is the basis of every Bluebird KPI.

Docs: https://open-meteo.com/en/docs/ensemble-api
"""

from __future__ import annotations

from typing import ClassVar

from ._open_meteo import OpenMeteoExtractor, OpenMeteoParams
from .base import ExtractorParams, register_extractor


class OpenMeteoEnsembleParams(OpenMeteoParams):
    base_url: str = "https://ensemble-api.open-meteo.com/v1/ensemble"


@register_extractor("open_meteo_ensemble")
class ExtractorOpenMeteoEnsemble(OpenMeteoExtractor):
    """Hourly ensemble members per station and elevation band."""

    Params: ClassVar[type[ExtractorParams]] = OpenMeteoEnsembleParams
