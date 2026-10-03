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


def test_one_request_per_station_with_one_location_per_band(ctx: RunContext) -> None:
    seen: list[dict[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append({k: v[0] for k, v in parse_qs(request.url.query.decode()).items()})
        return httpx.Response(200, json=[{"hourly": {}}, {"hourly": {}}])

    source = _source(ctx, "open_meteo_ensemble")
    extractor = EXTRACTORS.get("open_meteo_ensemble")(
        source, httpx.Client(transport=httpx.MockTransport(handler))
    )
    records = extractor.extract(ctx)

    assert [r.station_id for r in records] == ["alpha", "beta"]
    assert seen[0]["elevation"] == "2000,2500"  # mid, summit of Alpha
    assert seen[0]["models"] == "ecmwf_ifs025,icon_seamless"
    assert seen[0]["timezone"] == "UTC"
    assert records[0].context["bands"] == ["mid", "summit"]
    assert records[0].context["elevations"] == [2000, 2500]


def test_rate_limit_is_waited_out_then_retried(ctx: RunContext) -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(429, json={"reason": "Minutely API request limit exceeded"})
        return httpx.Response(200, json=[{}, {}, {}])

    source = _source(ctx, "open_meteo_forecast", rate_limit_wait_s=0)
    extractor = EXTRACTORS.get("open_meteo_forecast")(
        source, httpx.Client(transport=httpx.MockTransport(handler))
    )
    records = extractor.extract(ctx)
    assert len(records) == 2
    assert calls["n"] == 3  # 429 + retry for the first station, 1 call for the second


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
