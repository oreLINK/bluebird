"""Reference data is fetched once, committed under config/reference/, and read on any date."""

from __future__ import annotations

import shutil
from datetime import UTC, date, datetime

import httpx
from _factories import overpass_transport

from bluebird_pipeline.cli import main
from bluebird_pipeline.config import Config
from bluebird_pipeline.context import RunContext
from bluebird_pipeline.reference import missing_references, refresh_references
from bluebird_pipeline.storage import LocalStorage

REFERENCE_FILE = "reference/domain_features/pyrenees.geojson"


def _reference_sources(config: Config):
    return [
        s.model_copy(update={"params": {**s.params, "min_interval_s": 0}})
        for s in config.enabled_sources(schedule="reference")
    ]


def _clean(config: Config) -> None:
    shutil.rmtree(config.root / "reference", ignore_errors=True)


def test_refresh_writes_a_committed_file_read_on_any_later_date(ctx: RunContext) -> None:
    _clean(ctx.config)
    assert missing_references(ctx.config) == [REFERENCE_FILE]

    calls: list[str] = []
    report = refresh_references(
        ctx, _reference_sources(ctx.config), http=httpx.Client(transport=overpass_transport(calls))
    )
    assert report.errors == []
    assert calls == ["alpha", "beta"]
    assert (ctx.config.root / REFERENCE_FILE).is_file()
    assert missing_references(ctx.config) == []

    # A month later, a different run reads the same file without any network call.
    later = RunContext.create(
        ctx.config,
        LocalStorage(ctx.storage.root.parent / "other-storage"),  # type: ignore[attr-defined]
        run_date=date(2027, 1, 20),
        now=datetime(2027, 1, 20, 4, 30, tzinfo=UTC),
    )
    domains = later.reference("domain_features")
    assert domains is not None
    assert sorted(set(domains["station_id"])) == ["alpha", "beta"]
    assert domains.height == 4  # one piste and one lift per station


def test_no_fetch_rebuilds_from_the_latest_stored_bronze(ctx: RunContext) -> None:
    _clean(ctx.config)
    sources = _reference_sources(ctx.config)
    refresh_references(ctx, sources, http=httpx.Client(transport=overpass_transport()))
    path = ctx.config.root / REFERENCE_FILE
    path.unlink()

    def fail(request: httpx.Request) -> httpx.Response:
        raise AssertionError("must not call the network")

    report = refresh_references(
        ctx, sources, fetch=False, http=httpx.Client(transport=httpx.MockTransport(fail))
    )
    assert report.errors == []
    assert path.is_file()


def test_failed_fetch_keeps_the_previous_file(ctx: RunContext) -> None:
    _clean(ctx.config)
    sources = _reference_sources(ctx.config)
    refresh_references(ctx, sources, http=httpx.Client(transport=overpass_transport()))
    path = ctx.config.root / REFERENCE_FILE
    before = path.read_bytes()

    broken = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(400)))
    report = refresh_references(ctx, sources, http=broken)
    assert any(e.startswith("bronze/osm_overpass") for e in report.errors)
    assert path.read_bytes() == before


def test_daily_run_never_fetches_reference_sources(ctx: RunContext, tmp_path) -> None:
    assert "osm_overpass" not in [s.id for s in ctx.config.enabled_sources(schedule="daily")]
    code = main(
        [
            "--config-dir",
            str(ctx.config.root),
            "run",
            "--source",
            "osm_overpass",
            "--data-dir",
            str(tmp_path),
        ]
    )
    assert code == 2


def test_reference_is_none_before_the_first_refresh(ctx: RunContext) -> None:
    _clean(ctx.config)
    assert ctx.reference("domain_features") is None
