"""Météo-France avalanche bulletins: one request per massif, the key in a header only."""

from __future__ import annotations

from datetime import UTC, datetime
from urllib.parse import parse_qs

import httpx
import pytest

from bluebird_pipeline.bronze import EXTRACTORS
from bluebird_pipeline.bronze.extractor_meteofrance_bra import API_KEY_ENV
from bluebird_pipeline.config import Config
from bluebird_pipeline.context import RunContext
from bluebird_pipeline.storage import LocalStorage

KEY = "test-key-not-a-secret"
PYRENEES_MASSIFS = [64, 65, 66, 67, 68, 69, 70, 72, 73]  # of the 18 resorts


def _extractor(ctx: RunContext, handler):
    source = next(s for s in ctx.config.sources if s.id == "meteofrance_bra")
    source = source.model_copy(update={"params": {**source.params, "min_interval_s": 0}})
    extractor = EXTRACTORS.get("meteofrance_bra")(
        source, httpx.Client(transport=httpx.MockTransport(handler))
    )
    extractor.backoff_seconds = 0
    return extractor


@pytest.fixture
def ctx(repo_config: Config, tmp_path) -> RunContext:
    return RunContext.create(
        repo_config, LocalStorage(tmp_path), now=datetime(2027, 1, 15, 5, 7, tzinfo=UTC)
    )


@pytest.fixture(autouse=True)
def api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(API_KEY_ENV, KEY)


def test_one_request_per_avalanche_massif(ctx: RunContext) -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        number = parse_qs(request.url.query.decode())["id-massif"][0]
        return httpx.Response(200, text=f'<BULLETINS_NEIGE_AVALANCHE ID="{number}"/>')

    records = _extractor(ctx, handler).extract(ctx)

    assert [r.context["massif_number"] for r in records] == PYRENEES_MASSIFS
    assert all(r.url.path == "/public/DPBRA/v1/massif/BRA" for r in seen)
    assert all(r.headers["apikey"] == KEY for r in seen)
    assert records[0].params == {"id-massif": 64, "format": "xml"}
    assert records[0].payload == '<BULLETINS_NEIGE_AVALANCHE ID="64"/>'
    # The key never reaches the stored records.
    assert all(KEY not in r.model_dump_json() for r in records)


def test_no_bulletin_out_of_season_is_not_an_error(ctx: RunContext) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="Not Found")

    records = _extractor(ctx, handler).extract(ctx)
    assert len(records) == len(PYRENEES_MASSIFS)
    assert all(r.payload is None and r.status_code == 404 for r in records)


def test_a_refused_key_fails_at_once(ctx: RunContext) -> None:
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(401, text="Invalid Credentials")

    with pytest.raises(RuntimeError, match=f"refused the API key.*{API_KEY_ENV}"):
        _extractor(ctx, handler).extract(ctx)
    assert len(calls) == 1


def test_a_missing_key_fails(ctx: RunContext, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(API_KEY_ENV)
    with pytest.raises(RuntimeError, match=f"{API_KEY_ENV} is not set"):
        _extractor(ctx, lambda request: httpx.Response(200)).extract(ctx)


def test_a_failing_massif_is_skipped_but_not_all(ctx: RunContext) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        number = parse_qs(request.url.query.decode())["id-massif"][0]
        return httpx.Response(502) if number == "66" else httpx.Response(200, text="<x/>")

    records = _extractor(ctx, handler).extract(ctx)
    assert 66 not in [r.context["massif_number"] for r in records]
    assert len(records) == len(PYRENEES_MASSIFS) - 1

    with pytest.raises(RuntimeError, match="no avalanche bulletin fetched"):
        _extractor(ctx, lambda request: httpx.Response(503)).extract(ctx)
