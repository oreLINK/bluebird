"""Météo-France avalanche bulletins (BRA), one per avalanche massif.

API ``DonneesPubliquesBRA`` of the Météo-France portal: ``GET /massif/BRA``
with ``id-massif`` and ``format=xml`` returns the bulletin in force for one
massif. The API key comes from the environment (GitHub secret
``METEOFRANCE_BRA_API_KEY``) and is sent in the ``apikey`` header; it never
appears in the stored records.

One request per avalanche massif of the enabled stations (``avalanche_massif``
in the stations files), the XML stored as is. A massif without a bulletin
(out of season: bulletins run from early November to late May) answers 404
or an empty body: the record keeps a null payload and the run carries on. An
expired or wrong key (401/403) fails the source at once with a clear message;
other errors skip that massif, and fail the source only if every massif
failed.
"""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime
from typing import ClassVar

import httpx
from pydantic import Field

from ..context import RunContext
from .base import BronzeRecord, Extractor, ExtractorParams, register_extractor

log = logging.getLogger(__name__)

API_KEY_ENV = "METEOFRANCE_BRA_API_KEY"

#: Answers that mean "no bulletin for this massif right now", not a failure.
NO_BULLETIN = {204, 404}


class MeteofranceBraParams(ExtractorParams):
    base_url: str = Field(
        default="https://public-api.meteofrance.fr/public/DPBRA/v1",
        description="Base URL of the DonneesPubliquesBRA API.",
    )


@register_extractor("meteofrance_bra")
class ExtractorMeteofranceBra(Extractor):
    """Raw XML bulletins of the avalanche massifs of the run's stations."""

    Params: ClassVar[type[ExtractorParams]] = MeteofranceBraParams
    params: MeteofranceBraParams

    def extract(self, ctx: RunContext) -> list[BronzeRecord]:
        key = os.environ.get(API_KEY_ENV, "").strip()
        if not key:
            raise RuntimeError(f"{API_KEY_ENV} is not set: no avalanche bulletin fetched")
        numbers = sorted(
            {
                ref.station.avalanche_massif
                for ref in ctx.stations()
                if ref.station.avalanche_massif is not None
            }
        )
        url = f"{self.params.base_url.rstrip('/')}/massif/BRA"
        records: list[BronzeRecord] = []
        errors: list[str] = []
        for number in numbers:
            params = {"id-massif": number, "format": "xml"}
            try:
                response = self._request("GET", url, params=params, headers={"apikey": key})
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                if status in NO_BULLETIN:
                    response = exc.response
                elif status in (401, 403):
                    raise RuntimeError(
                        f"Météo-France refused the API key (HTTP {status}): check that "
                        f"{API_KEY_ENV} is set and has not expired"
                    ) from None
                else:
                    errors.append(f"massif {number}: HTTP {status}")
                    log.warning("%s: massif %d: HTTP %d", self.id, number, status)
                    continue
            except httpx.TransportError as exc:
                errors.append(f"massif {number}: {exc}")
                log.warning("%s: massif %d: %s", self.id, number, exc)
                continue
            text = response.text.strip()
            records.append(
                BronzeRecord(
                    source_id=self.source.id,
                    url=url,
                    params=params,
                    context={"massif_number": number},
                    fetched_at=datetime.now(UTC),
                    status_code=response.status_code,
                    payload=text if response.status_code not in NO_BULLETIN and text else None,
                )
            )
        if numbers and not records:
            raise RuntimeError("no avalanche bulletin fetched: " + "; ".join(errors))
        return records
