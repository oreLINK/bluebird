from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest
from _factories import RUN_DATE, overpass_payload

from bluebird_pipeline.bronze import BronzeBatch, BronzeRecord
from bluebird_pipeline.context import RunContext
from bluebird_pipeline.silver import TRANSFORMERS
from bluebird_pipeline.silver.transformer_osm_overpass import path_length_m


def _batch() -> BronzeBatch:
    return BronzeBatch(
        source_id="osm_overpass",
        run_id="20261214T043000Z",
        run_date=RUN_DATE,
        records=[
            BronzeRecord(
                source_id="osm_overpass",
                station_id=station_id,
                url="https://overpass-api.de/api/interpreter",
                fetched_at=datetime(2026, 12, 14, tzinfo=UTC),
                status_code=200,
                payload=overpass_payload(station_id),
            )
            for station_id in ("alpha", "beta")
        ],
    )


def _transformer(ctx: RunContext):
    source = next(s for s in ctx.config.sources if s.id == "osm_overpass")
    return TRANSFORMERS.get("osm_overpass")(source)


def test_pistes_and_lifts_keep_their_geometry(ctx: RunContext) -> None:
    frame = _transformer(ctx).transform(_batch(), ctx)

    alpha = frame.filter(frame["station_id"] == "alpha")
    assert alpha["feature"].to_list() == ["lift", "piste"]  # sorted; station and node dropped
    piste = alpha.filter(alpha["feature"] == "piste").row(0, named=True)
    assert piste["kind"] == "easy"
    assert piste["coordinates"][0] == [0.1, 42.8]
    assert piste["length_m"] == pytest.approx(path_length_m(piste["coordinates"]), abs=0.1)
    assert 200 < piste["length_m"] < 250  # 0.002° of latitude ≈ 222 m


def test_reference_file_is_deterministic_and_round_trips(ctx: RunContext) -> None:
    transformer = _transformer(ctx)
    frame = transformer.transform(_batch(), ctx)
    massif = ctx.massifs()[0]

    content = transformer.reference_file(frame, massif, ctx)
    assert content is not None
    assert content == transformer.reference_file(frame.reverse(), massif, ctx)

    collection = json.loads(content)
    assert collection["type"] == "FeatureCollection"
    assert collection["bluebird"]["summary"]["alpha"] == {
        "lift_km": 0.3,
        "lifts": 1,
        "piste_km": 0.2,
        "piste_km_by_difficulty": {"easy": 0.2},
        "pistes": 1,
    }
    first = collection["features"][0]
    assert first["geometry"]["type"] == "LineString"
    assert first["id"].startswith("way/")
    # One feature per line keeps refresh diffs readable.
    lines = content.decode().splitlines()
    assert sum(line.startswith('{"type":"Feature"') for line in lines) == len(
        collection["features"]
    )

    back = transformer.read_reference(content)
    assert back.columns == frame.columns
    assert (
        back.sort("station_id", "osm_id")["osm_id"].to_list()
        == frame.sort("station_id", "osm_id")["osm_id"].to_list()
    )


def test_massif_without_rows_produces_no_file(ctx: RunContext) -> None:
    transformer = _transformer(ctx)
    frame = transformer.transform(_batch(), ctx).clear()
    assert transformer.reference_file(frame, ctx.massifs()[0], ctx) is None
