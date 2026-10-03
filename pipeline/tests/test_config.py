from __future__ import annotations

from datetime import time
from pathlib import Path

import pytest
from _factories import TWO_STATIONS, tiny_config_dir

from bluebird_pipeline.checks import plugin_errors
from bluebird_pipeline.config import Config, ConfigError, Elevation, load_config


def test_repository_config_is_valid(repo_config: Config) -> None:
    assert repo_config.reference_errors() == []
    assert plugin_errors(repo_config) == []
    assert len(repo_config.station_refs()) >= 15


def test_station_defaults_are_resolved(two_station_config: Config) -> None:
    alpha, beta = two_station_config.station_refs()
    assert (alpha.grooming_end, alpha.lifts_open) == (time(2, 0), time(9, 0))
    assert beta.grooming_end == time(22, 0)  # station override


def test_mid_elevation_defaults_to_rounded_average() -> None:
    assert Elevation(base=1420, summit=2600).at("mid") == 2010
    assert Elevation(base=1420, summit=2600, mid=1900).at("mid") == 1900


@pytest.mark.parametrize(
    ("bad_yaml", "message"),
    [
        (TWO_STATIONS.replace("name: Alpha", "name: Alpha\n    altitude: 3"), "Extra inputs"),
        (TWO_STATIONS.replace("summit: 2500", "summit: 1000"), "summit must be higher"),
        (TWO_STATIONS.replace('lifts_open: "09:00"', 'lifts_open: "9h"'), "String should match"),
        (TWO_STATIONS.replace("id: beta", "id: alpha"), "duplicate station id"),
    ],
)
def test_invalid_stations_are_rejected(tmp_path: Path, bad_yaml: str, message: str) -> None:
    with pytest.raises(ConfigError, match=message):
        load_config(tiny_config_dir(tmp_path, bad_yaml))


def test_layout_must_reference_existing_tiles(tmp_path: Path) -> None:
    config_dir = tiny_config_dir(tmp_path)
    (config_dir / "layout.yaml").write_text("default: [snowfall_today, nope]\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="unknown tile 'nope'"):
        load_config(config_dir)


def test_massif_without_station_file_is_rejected(tmp_path: Path) -> None:
    config_dir = tiny_config_dir(tmp_path)
    (config_dir / "stations" / "pyrenees.yaml").rename(config_dir / "stations" / "alps.yaml")
    with pytest.raises(ConfigError, match=r"has no config/stations/pyrenees\.yaml"):
        load_config(config_dir)


def test_unknown_aggregator_and_bad_params_are_reported(tmp_path: Path) -> None:
    config_dir = tiny_config_dir(tmp_path)
    kpis = (config_dir / "kpis.yaml").read_text(encoding="utf-8")
    kpis = kpis.replace("aggregator: onpiste_powder_chance", "aggregator: does_not_exist")
    kpis = kpis.replace("threshold_cm: 1.0", "threshold_cm: -1")
    (config_dir / "kpis.yaml").write_text(kpis, encoding="utf-8")
    errors = plugin_errors(load_config(config_dir))
    assert any("unknown aggregator 'does_not_exist'" in e for e in errors)
    assert any("snowfall_chance' params" in e for e in errors)


def test_committed_reference_files_cover_every_station(repo_config: Config) -> None:
    from bluebird_pipeline.reference import load_reference, missing_references

    assert missing_references(repo_config) == [], "run `uv run bluebird reference`"
    domains = load_reference(repo_config, "domain_features")
    assert domains is not None
    stations = {ref.id for ref in repo_config.station_refs()}
    assert set(domains["station_id"]) == stations, "a station has no piste or lift"
