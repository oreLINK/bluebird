"""Bronze layer contract: ``Extractor`` classes fetch raw data from one source.

Bronze data is stored exactly as received (plus request metadata), gzip
compressed, one batch per source and run. It is never modified afterwards, so
silver, gold and diamond can always be rebuilt from it.
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from datetime import UTC, date, datetime
from typing import Any, ClassVar

import httpx
from pydantic import BaseModel, ConfigDict, Field

from ..config import Source
from ..context import RunContext
from ..registry import Registry

log = logging.getLogger(__name__)

USER_AGENT = "bluebird-pipeline/0.1 (+https://github.com/; ski weather KPIs)"


class BronzeRecord(BaseModel):
    """One raw response, with enough metadata to reproduce the request."""

    source_id: str
    station_id: str | None = None
    url: str
    params: dict[str, Any] = Field(default_factory=dict)
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Extractor metadata the transformer needs (e.g. requested bands).",
    )
    fetched_at: datetime
    status_code: int
    payload: Any


class BronzeBatch(BaseModel):
    """All records of one source for one run: the unit stored in bronze."""

    source_id: str
    run_id: str
    run_date: date
    records: list[BronzeRecord]


class ExtractorParams(BaseModel):
    """Base class of every Extractor ``Params`` model (unknown keys rejected).

    The throttling fields apply to every extractor that uses the HTTP helpers.
    """

    model_config = ConfigDict(extra="forbid")

    min_interval_s: float = Field(
        default=0.0, ge=0, description="Minimum delay between two requests (politeness)."
    )
    rate_limit_wait_s: float = Field(
        default=65.0, ge=0, description="Delay before retrying after HTTP 429."
    )
    max_rate_limit_waits: int = Field(default=4, ge=0, le=20)


class Extractor(ABC):
    """Fetch raw data for one source.

    Subclasses set a nested ``Params`` model (validated from ``sources.yaml``),
    implement :meth:`extract`, and register with ``@register_extractor("id")``.
    """

    id: ClassVar[str]
    Params: ClassVar[type[ExtractorParams]] = ExtractorParams

    max_attempts: ClassVar[int] = 3
    backoff_seconds: ClassVar[float] = 2.0

    def __init__(self, source: Source, http: httpx.Client) -> None:
        self.source = source
        self.http = http
        self.params = self.Params.model_validate(source.params)
        self._last_request_at: float | None = None

    @abstractmethod
    def extract(self, ctx: RunContext) -> list[BronzeRecord]:
        """Return the raw records for this run. Must not transform the payloads."""

    # -- helpers ---------------------------------------------------------------

    def get_json(
        self,
        url: str,
        params: dict[str, Any],
        *,
        station_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> BronzeRecord:
        """GET ``url`` with retries on transient errors and wrap the JSON response."""
        response = self._request("GET", url, params=params)
        return self._record(url, params, response, station_id, context)

    def post_form(
        self,
        url: str,
        data: dict[str, Any],
        *,
        station_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> BronzeRecord:
        """POST form ``data`` to ``url`` with retries and wrap the JSON response."""
        response = self._request("POST", url, data=data)
        return self._record(url, data, response, station_id, context)

    def _record(
        self,
        url: str,
        params: dict[str, Any],
        response: httpx.Response,
        station_id: str | None,
        context: dict[str, Any] | None,
    ) -> BronzeRecord:
        return BronzeRecord(
            source_id=self.source.id,
            station_id=station_id,
            url=url,
            params=params,
            context=context or {},
            fetched_at=datetime.now(UTC),
            status_code=response.status_code,
            payload=response.json(),
        )

    def _throttle(self) -> None:
        interval = self.params.min_interval_s
        if interval and self._last_request_at is not None:
            elapsed = time.monotonic() - self._last_request_at
            if elapsed < interval:
                time.sleep(interval - elapsed)
        self._last_request_at = time.monotonic()

    def _request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        """Send a request, retrying server/transport errors and waiting out rate limits."""
        failures = 0
        rate_limit_waits = 0
        while True:
            self._throttle()
            try:
                response = self.http.request(method, url, **kwargs)
            except httpx.TransportError as exc:
                failures += 1
                if failures >= self.max_attempts:
                    raise
                delay = self.backoff_seconds * failures
                log.warning("%s: %s, retrying in %.0fs", self.id, exc, delay)
                time.sleep(delay)
                continue

            if response.status_code == 429:
                rate_limit_waits += 1
                if rate_limit_waits > self.params.max_rate_limit_waits:
                    response.raise_for_status()
                delay = _retry_after(response) or self.params.rate_limit_wait_s
                log.warning("%s: rate limited (HTTP 429), waiting %.0fs", self.id, delay)
                time.sleep(delay)
                continue

            if response.status_code >= 500:
                failures += 1
                if failures >= self.max_attempts:
                    response.raise_for_status()
                delay = self.backoff_seconds * failures
                log.warning("%s: HTTP %d, retrying in %.0fs", self.id, response.status_code, delay)
                time.sleep(delay)
                continue

            response.raise_for_status()
            return response


def _retry_after(response: httpx.Response) -> float | None:
    """Seconds from a numeric ``Retry-After`` header, if any."""
    value = response.headers.get("Retry-After", "")
    try:
        return max(0.0, float(value))
    except ValueError:
        return None


def default_http_client() -> httpx.Client:
    """HTTP client used by the CLI (tests inject their own)."""
    return httpx.Client(timeout=httpx.Timeout(60.0), headers={"User-Agent": USER_AGENT})


EXTRACTORS: Registry[Extractor] = Registry("extractor")
register_extractor = EXTRACTORS.register
