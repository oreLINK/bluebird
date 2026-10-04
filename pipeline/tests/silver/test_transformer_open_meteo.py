from __future__ import annotations

from datetime import UTC, datetime, timedelta

import polars as pl
import pytest
from _factories import RUN_DATE, hourly_times, open_meteo_location

from bluebird_pipeline.bronze import BronzeBatch, BronzeRecord
from bluebird_pipeline.context import RunContext
from bluebird_pipeline.silver import TRANSFORMERS
from bluebird_pipeline.silver._open_meteo import OpenMeteoParseError, parse_series_key

MODELS = ["ecmwf_ifs025", "icon_seamless"]
VARS = ["snowfall", "temperature_2m", "wind_speed_10m"]


@pytest.mark.parametrize(
    ("key", "models", "expected"),
    [
        ("snowfall", ["ecmwf_ifs025"], ("snowfall", 0, "ecmwf_ifs025")),
        ("snowfall_member07", ["ecmwf_ifs025"], ("snowfall", 7, "ecmwf_ifs025")),
        ("snowfall_member07_ecmwf_ifs025_ensemble", MODELS, ("snowfall", 7, "ecmwf_ifs025")),
        ("snowfall_icon_seamless_eps", MODELS, ("snowfall", 0, "icon_seamless")),
        (
            "temperature_2m_member39_icon_seamless_eps",
            MODELS,
            ("temperature_2m", 39, "icon_seamless"),
        ),
        ("snowfall_unknown_model", MODELS, None),
        ("snowfall", MODELS, None),  # ambiguous without a model suffix
        ("snow_depth", ["ecmwf_ifs025"], None),
    ],
)
def test_parse_series_key(key: str, models: list[str], expected: tuple | None) -> None:
    assert parse_series_key(key, VARS, models) == expected


def _batch(locations: list[dict], bands: list[str], elevations: list[int]) -> BronzeBatch:
    return BronzeBatch(
        source_id="open_meteo_ensemble",
        run_id="20261214T043000Z",
        run_date=RUN_DATE,
        records=[
            BronzeRecord(
                source_id="open_meteo_ensemble",
                station_id="alpha",
                url="https://ensemble-api.open-meteo.com/v1/ensemble",
                context={
                    "bands": bands,
                    "elevations": elevations,
                    "models": MODELS,
                    "hourly": VARS,
                },
                fetched_at=datetime(2026, 12, 14, tzinfo=UTC),
                status_code=200,
                payload=locations,
            )
        ],
    )


def test_ensemble_batch_becomes_one_row_per_member_and_hour(ctx: RunContext) -> None:
    times = hourly_times(RUN_DATE, 1)
    locations = [
        open_meteo_location(times=times, elevation=e, variables=VARS, models=MODELS, ensemble=True)
        for e in (2000, 2500)
    ]
    transformer = TRANSFORMERS.get("open_meteo_ensemble")(ctx.config.sources[0])
    frame = transformer.transform(_batch(locations, ["mid", "summit"], [2000, 2500]), ctx)

    members = 51 + 40  # ECMWF control + 50, ICON control + 39
    assert frame.height == 2 * members * 24
    assert list(frame.columns) == list(transformer.schema)
    first = frame.row(0, named=True)
    assert first["time_utc"] == datetime(2026, 12, 14, 0, tzinfo=UTC)
    assert first["snowfall_cm"] == pytest.approx(0.4)
    assert frame["precipitation_mm"].null_count() == frame.height  # not requested -> null
    assert set(frame["model"].unique()) == set(MODELS)
    assert frame.filter(frame["model"] == "icon_seamless")["member"].max() == 39


def test_unit_mismatch_is_rejected(ctx: RunContext) -> None:
    location = open_meteo_location(
        times=hourly_times(RUN_DATE, 1),
        elevation=2000,
        variables=VARS,
        models=MODELS,
        ensemble=False,
    )
    location["hourly_units"]["snowfall_ecmwf_ifs025_ensemble"] = "inch"
    transformer = TRANSFORMERS.get("open_meteo_ensemble")(ctx.config.sources[0])
    with pytest.raises(OpenMeteoParseError, match="'inch', expected 'cm'"):
        transformer.transform(_batch([location], ["mid"], [2000]), ctx)


def test_location_count_must_match_bands(ctx: RunContext) -> None:
    location = open_meteo_location(
        times=hourly_times(RUN_DATE - timedelta(days=1), 1),
        elevation=2000,
        variables=VARS,
        models=MODELS,
        ensemble=False,
    )
    transformer = TRANSFORMERS.get("open_meteo_ensemble")(ctx.config.sources[0])
    with pytest.raises(OpenMeteoParseError, match="expected 2 locations"):
        transformer.transform(_batch([location], ["mid", "summit"], [2000, 2500]), ctx)


def test_grouped_request_maps_each_location_to_its_station(ctx: RunContext) -> None:
    times = hourly_times(RUN_DATE, 1)
    locations = [
        open_meteo_location(times=times, elevation=e, variables=VARS, models=MODELS, ensemble=False)
        for e in (2000, 1800)
    ]
    batch = _batch(locations, [], [])
    batch.records[0] = batch.records[0].model_copy(
        update={
            "station_id": None,
            "context": {
                "locations": [
                    {"station_id": "alpha", "band": "mid", "elevation": 2000},
                    {"station_id": "beta", "band": "mid", "elevation": 1800},
                ],
                "models": MODELS,
                "hourly": VARS,
            },
        }
    )
    transformer = TRANSFORMERS.get("open_meteo_ensemble")(ctx.config.sources[0])
    frame = transformer.transform(batch, ctx)

    by_station = dict(frame.group_by("station_id").agg(pl.col("elevation_m").first()).iter_rows())
    assert by_station == {"alpha": 2000, "beta": 1800}
