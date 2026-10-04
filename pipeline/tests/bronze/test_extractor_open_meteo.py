from __future__ import annotations

from urllib.parse import parse_qs

import httpx
import pytest

from bluebird_pipeline.bronze import EXTRACTORS
from bluebird_pipeline.context import RunContext


def _source(ctx: RunContext, source_id: str, **overrides: object):
    source = next(s for s in ctx.config.sources if s.id == source_id)
    params = {**source.params, "min_interval_s": 0, **overrides}
    return source.model_copy(update={"params": params})


def _record_queries(response_locations: int | None = None):
    seen: list[dict[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        query = {k: v[0] for k, v in parse_qs(request.url.query.decode()).items()}
        seen.append(query)
        count = response_locations or len(query["elevation"].split(","))
        return httpx.Response(200, json=[{"hourly": {}}] * count)

    return seen, httpx.Client(transport=httpx.MockTransport(handler))


def test_one_request_for_every_station_and_band(ctx: RunContext) -> None:
    seen, http = _record_queries()
    source = _source(ctx, "open_meteo_ensemble")
    records = EXTRACTORS.get("open_meteo_ensemble")(source, http).extract(ctx)

    assert len(seen) == len(records) == 1
    # Alpha mid, Alpha summit, Beta mid, Beta summit.
    assert seen[0]["elevation"] == "2000,2500,1800,2200"
    assert seen[0]["latitude"] == "42.8,42.8,42.9,42.9"
    assert seen[0]["models"] == "ecmwf_ifs025,icon_seamless"
    assert seen[0]["timezone"] == "UTC"
    assert records[0].station_id is None
    assert records[0].context["locations"] == [
        {"station_id": "alpha", "band": "mid", "elevation": 2000},
        {"station_id": "alpha", "band": "summit", "elevation": 2500},
        {"station_id": "beta", "band": "mid", "elevation": 1800},
        {"station_id": "beta", "band": "summit", "elevation": 2200},
    ]


def test_locations_can_be_split_in_batches(ctx: RunContext) -> None:
    seen, http = _record_queries()
    source = _source(ctx, "open_meteo_forecast", max_locations_per_request=4)
    records = EXTRACTORS.get("open_meteo_forecast")(source, http).extract(ctx)

    # 2 stations x 3 bands = 6 locations -> 4 + 2.
    assert [len(q["elevation"].split(",")) for q in seen] == [4, 2]
    assert [len(r.context["locations"]) for r in records] == [4, 2]


def test_rate_limit_is_waited_out_then_retried(ctx: RunContext) -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(429, json={"reason": "Minutely API request limit exceeded"})
        return httpx.Response(200, json=[{}] * 6)

    source = _source(ctx, "open_meteo_forecast", rate_limit_wait_s=0)
    extractor = EXTRACTORS.get("open_meteo_forecast")(
        source, httpx.Client(transport=httpx.MockTransport(handler))
    )
    records = extractor.extract(ctx)
    assert len(records) == 1
    assert calls["n"] == 2  # 429, then the retry


def test_client_errors_are_not_retried(ctx: RunContext) -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(400, json={"reason": "bad variable"})

    source = _source(ctx, "open_meteo_forecast")
    extractor = EXTRACTORS.get("open_meteo_forecast")(
        source, httpx.Client(transport=httpx.MockTransport(handler))
    )
    with pytest.raises(httpx.HTTPStatusError):
        extractor.extract(ctx)
    assert calls["n"] == 1


def test_unknown_param_is_rejected(ctx: RunContext) -> None:
    source = _source(ctx, "open_meteo_forecast", typo_param=1)
    with pytest.raises(ValueError, match="typo_param"):
        EXTRACTORS.get("open_meteo_forecast")(source, httpx.Client())
