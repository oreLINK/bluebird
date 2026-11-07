"""Each tile cites only the sources of its own KPI, derived from its aggregator."""

from __future__ import annotations

import inspect
import re
import sys

from bluebird_pipeline.config import Config
from bluebird_pipeline.diamond._payload import kpi_source_ids
from bluebird_pipeline.gold import AGGREGATORS


def test_live_kpis_cite_the_source_of_their_dataset(repo_config: Config) -> None:
    assert kpi_source_ids(repo_config, repo_config.kpi("wind_chill_chance")) == [
        "open_meteo_ensemble"
    ]
    # Snow also reads the deterministic AROME forecast when it is there.
    assert kpi_source_ids(repo_config, repo_config.kpi("snowfall_chance")) == [
        "open_meteo_ensemble",
        "open_meteo_forecast",
    ]
    # The avalanche danger relays the bulletin only: no Open-Meteo source.
    assert kpi_source_ids(repo_config, repo_config.kpi("avalanche_risk")) == ["meteofrance_bra"]


def test_every_enabled_kpi_has_a_source(repo_config: Config) -> None:
    missing = [k.id for k in repo_config.kpis if k.enabled and not kpi_source_ids(repo_config, k)]
    assert missing == []


def test_rewind_kpis_cite_the_season_sources_of_their_columns(repo_config: Config) -> None:
    def ids(kpi_id: str) -> list[str]:
        return kpi_source_ids(repo_config, repo_config.kpi(kpi_id))

    assert ids("season_total_snowfall") == ["open_meteo_historical"]
    # Domain points are placed along the OpenStreetMap pistes.
    assert ids("season_domain_snowfall") == ["open_meteo_historical", "osm_overpass"]
    assert ids("season_deep_snow_days") == ["open_meteo_historical_snowpack", "osm_overpass"]
    assert ids("season_white_days") == [
        "open_meteo_historical",
        "open_meteo_historical_light",
        "osm_overpass",
    ]


def test_aggregators_declare_every_dataset_they_read() -> None:
    """A dataset read but not declared would be missing from the tile's sources."""
    for agg_id, cls in AGGREGATORS.items():
        if getattr(cls, "kind", "live") != "live":
            continue
        code = inspect.getsource(sys.modules[cls.__module__])
        read = set(re.findall(r"""silver(?:_optional)?\(\s*["']([a-z_]+)["']""", code))
        declared = {*cls.required_datasets, *getattr(cls, "optional_datasets", ())}
        assert read <= declared, (agg_id, read - declared)
