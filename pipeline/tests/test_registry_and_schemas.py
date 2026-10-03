from __future__ import annotations

import pytest

from bluebird_pipeline.bronze import EXTRACTORS
from bluebird_pipeline.diamond import DISPLAYERS
from bluebird_pipeline.gold import AGGREGATORS
from bluebird_pipeline.paths import repo_root
from bluebird_pipeline.registry import Registry, RegistryError
from bluebird_pipeline.schemas import stale_schemas
from bluebird_pipeline.silver import TRANSFORMERS


def test_registry_rejects_duplicates_and_lists_available_ids() -> None:
    registry: Registry[object] = Registry("widget")

    @registry.register("one")
    class One: ...

    with pytest.raises(RegistryError, match="already registered"):

        @registry.register("one")
        class Other: ...

    with pytest.raises(RegistryError, match=r"unknown widget 'two' \(available: one\)"):
        registry.get("two")
    assert One.id == "one"  # type: ignore[attr-defined]


def test_every_layer_folder_is_autodiscovered() -> None:
    assert {"open_meteo_ensemble", "open_meteo_forecast", "osm_overpass"} <= set(EXTRACTORS.ids())
    assert {"open_meteo_ensemble", "open_meteo_forecast", "osm_overpass"} <= set(TRANSFORMERS.ids())
    assert {"snowfall_chance", "offpiste_powder_chance", "onpiste_powder_chance"} <= set(
        AGGREGATORS.ids()
    )
    assert "massif_daily" in DISPLAYERS


def test_class_names_follow_the_layer_prefix_convention() -> None:
    for prefix, registry in (
        ("Extractor", EXTRACTORS),
        ("Transformer", TRANSFORMERS),
        ("Aggregator", AGGREGATORS),
        ("Displayer", DISPLAYERS),
    ):
        for plugin_id, cls in registry.items():
            module = cls.__module__.rsplit(".", 1)[-1]
            assert cls.__name__.startswith(prefix), cls
            assert module.startswith(prefix.lower() + "_"), (plugin_id, module)


def test_committed_json_schemas_are_up_to_date() -> None:
    assert stale_schemas(repo_root() / "config" / "schemas") == [], (
        "run `uv run bluebird schemas` and commit the result"
    )
