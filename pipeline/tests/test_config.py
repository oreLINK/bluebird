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


def test_every_pyrenean_station_has_a_departement(repo_config: Config) -> None:
    pyrenees = next(m for m in repo_config.massifs if m.id == "pyrenees")
    assert [z.code for z in pyrenees.zones] == ["64", "65", "31", "09", "66"]
    zones = {s.zone for s in repo_config.stations["pyrenees"].stations}
    assert zones == {z.id for z in pyrenees.zones}


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
        (TWO_STATIONS.replace("zone: haute-garonne", "zone: savoie"), "needs a zone of massif"),
        (TWO_STATIONS.replace("    zone: hautes-pyrenees\n", ""), "has None"),
        (
            TWO_STATIONS.replace(
                "domain: alpha-beta\n    name: Beta", "domain: nope\n    name: Beta"
            ),
            "unknown domain 'nope'",
        ),
        (
            TWO_STATIONS.replace(
                "  - id: alpha-beta\n    name: Alpha-Beta\n",
                "  - id: alpha-beta\n    name: Alpha-Beta\n  - id: alpha-beta\n    name: Again\n",
            ),
            "duplicate massif 'pyrenees' domain id",
        ),
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


def test_duplicate_yaml_keys_are_rejected(tmp_path: Path) -> None:
    config_dir = tiny_config_dir(tmp_path)
    kpis = (config_dir / "kpis.yaml").read_text(encoding="utf-8")
    line = "    aggregator: snowfall_chance\n"
    (config_dir / "kpis.yaml").write_text(kpis.replace(line, line + line, 1), encoding="utf-8")
    with pytest.raises(ConfigError, match="duplicate key 'aggregator'"):
        load_config(config_dir)


def test_kpi_filters_must_exist_and_every_filter_must_match_a_kpi(tmp_path: Path) -> None:
    config_dir = tiny_config_dir(tmp_path)
    kpis = (config_dir / "kpis.yaml").read_text(encoding="utf-8")
    (config_dir / "kpis.yaml").write_text(kpis.replace("filters: [snow]", "filters: [snw]"))
    with pytest.raises(ConfigError) as error:
        load_config(config_dir)
    assert "KPI 'snowfall_chance' references unknown filter 'snw'" in str(error.value)
    assert "filter 'snow' matches no enabled KPI" in str(error.value)


@pytest.mark.parametrize(
    ("file", "old", "new", "message"),
    [
        (
            "layout.yaml",
            "{ tile: whiteout, period: day }",
            "{ tile: nope, period: day }",
            "layout 'home.fallback' references unknown tile 'nope'",
        ),
        (
            "layout.yaml",
            "{ tile: onpiste_powder, period: day }",
            "{ tile: onpiste_powder, period: evening }",
            "tile 'onpiste_powder' is not shown for period 'evening'",
        ),
        (
            "layout.yaml",
            "{ tile: whiteout, period: day }",
            "{ tile: rewind_2025_26_white_days, period: day }",
            "Rewind tile 'rewind_2025_26_white_days' cannot be on the home page",
        ),
        (
            "layout.yaml",
            "{ tile: whiteout, period: day }",
            "{ tile: onpiste_powder, period: day }",
            "duplicate layout 'home.fallback' entry id 'onpiste_powder@day'",
        ),
        (
            "filters.yaml",
            "levels: [group, day]\n",
            "levels: [group, day, day]\n",
            "only appear once",
        ),
        ("filters.yaml", "levels: [group, day]\n", "levels: [group, week]\n", "Input should be"),
        (
            "filters.yaml",
            "kpis: [easy_conditions_chance]",
            "kpis: [easy_conditions_chance, heavy_snow_chance]",
            "KPI 'heavy_snow_chance' is in several groups",
        ),
        (
            "filters.yaml",
            "kpis: [spring_snow_chance, hard_snow_chance, heavy_snow_chance]",
            "kpis: [spring_snow_chance, hard_snow_chance]",
            "KPI 'heavy_snow_chance' is in no group",
        ),
        (
            "filters.yaml",
            "kpis: [wind_chill_chance]",
            "kpis: [wind_chill_chance, chains_chance]",
            "group KPI 'chains_chance' is not tagged with it",
        ),
        ("filters.yaml", "levels: [group, day]\n", "levels: [day]\n", "`group` level and `groups`"),
        (
            "periods.yaml",
            "    chip: { fr: Nuit, en: Night, es: De madrugada }\n",
            "",
            "'night' needs a `chip`",
        ),
        (
            "periods.yaml",
            "  - { fr: Demain, en: Tomorrow, es: Mañana }\n",
            "",
            "`days` needs 2 chip labels",
        ),
    ],
)
def test_invalid_filter_levels_and_home_tiles_are_rejected(
    tmp_path: Path, file: str, old: str, new: str, message: str
) -> None:
    config_dir = tiny_config_dir(tmp_path)
    text = (config_dir / file).read_text(encoding="utf-8")
    assert old in text
    (config_dir / file).write_text(text.replace(old, new, 1), encoding="utf-8")
    with pytest.raises(ConfigError, match=message):
        load_config(config_dir)


def test_filters_have_at_most_four_levels(repo_config: Config) -> None:
    from bluebird_pipeline.config import MAX_FILTER_LEVELS, Filter

    with pytest.raises(ValueError, match="at most 3"):
        Filter.model_validate(
            {
                "id": "x",
                "name": {"fr": "x", "en": "x", "es": "x"},
                "levels": ["day", "slot", "day", "slot"],
            }
        )
    assert all(1 + len(f.levels) <= MAX_FILTER_LEVELS for f in repo_config.filters)


def test_bluebird_today_leads_the_home_page(repo_config: Config) -> None:
    home = repo_config.layout.home
    first = home.pinned[0]
    assert (first.tile, first.period) == ("bluebird_day", "day")
    assert home.mode == "scored"
    assert home.limit == 50


def test_every_live_kpi_competes_for_the_home_page(repo_config: Config) -> None:
    for kpi in repo_config.enabled_kpis(kind="live"):
        assert kpi.visibility is not None, kpi.id
        assert 0 < kpi.visibility.priority <= 1
    assert all(k.visibility is None for k in repo_config.enabled_kpis(kind="historical"))


@pytest.mark.parametrize(
    ("file", "old", "new", "message"),
    [
        (
            "kpis.yaml",
            "    visibility: { priority: 0.75, floor: 0.4, strong: 0.8 }\n",
            "",
            "live KPI 'whiteout_chance' needs `visibility`",
        ),
        (
            "kpis.yaml",
            "visibility: { priority: 0.75, floor: 0.4, strong: 0.8 }",
            "visibility: { priority: 0.75, floor: 40, strong: 80 }",
            "probability thresholds are between 0 and 1",
        ),
        (
            "kpis.yaml",
            "visibility: { priority: 0.75, floor: 0.4, strong: 0.8 }",
            "visibility: { priority: 0.75, measure: value, floor: 0.4, strong: 0.8 }",
            "measure `value` needs a `value` display",
        ),
        (
            "kpis.yaml",
            "visibility: { priority: 0.75, floor: 0.4, strong: 0.8 }",
            "visibility: { priority: 0.75, floor: 0.4, strong: 0.4 }",
            "`floor` and `strong` must differ",
        ),
        (
            "kpis.yaml",
            "slots: { floor: 2, strong: 15 }",
            "slots: { floor: 15, strong: 2 }",
            "`slots` thresholds go the other way",
        ),
        (
            "layout.yaml",
            '        - { from: "20:00", factor: 1.0 }\n',
            '        - { from: "16:00", factor: 1.0 }\n',
            "steps must follow the ski day clock",
        ),
        (
            "layout.yaml",
            '      from: "12:00"\n',
            '      from: "18:00"\n',
            "`from` must come before the first tomorrow step",
        ),
        (
            "layout.yaml",
            "      filters: [access]\n",
            "      filters: [acces]\n",
            "unknown filter 'acces'",
        ),
        (
            "layout.yaml",
            "      overnight:\n",
            "      morning:\n",
            "'morning' is not day-grain",
        ),
        (
            "layout.yaml",
            "  relevance:\n",
            "  relevanc:\n",
            "relevanc",
        ),
    ],
)
def test_invalid_visibility_settings_are_rejected(
    tmp_path: Path, file: str, old: str, new: str, message: str
) -> None:
    config_dir = tiny_config_dir(tmp_path)
    text = (config_dir / file).read_text(encoding="utf-8")
    assert old in text
    (config_dir / file).write_text(text.replace(old, new, 1), encoding="utf-8")
    with pytest.raises(ConfigError, match=message):
        load_config(config_dir)


def test_method_placeholders_must_be_kpi_params(tmp_path: Path) -> None:
    config_dir = tiny_config_dir(tmp_path)
    kpis = (config_dir / "kpis.yaml").read_text(encoding="utf-8")
    kpis = kpis.replace("{threshold_cm} cm.", "{threshold} cm.", 1)
    (config_dir / "kpis.yaml").write_text(kpis, encoding="utf-8")
    with pytest.raises(ConfigError, match=r"method \(fr\) uses '\{threshold\}'"):
        load_config(config_dir)


def test_short_name_is_published_with_a_fallback(repo_config: Config) -> None:
    refs = {ref.id: ref.station for ref in repo_config.station_refs()}
    assert refs["cauterets"].short_name == "Cauterets"
    assert all(len(s.short_name or s.name) <= 20 or s.short_name is None for s in refs.values())


def _edit(config_dir: Path, name: str, old: str, new: str) -> None:
    path = config_dir / name
    text = path.read_text(encoding="utf-8")
    assert old in text, old
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def test_repository_periods_cover_the_ski_day(repo_config: Config) -> None:
    periods = repo_config.periods
    assert periods.errors() == []
    assert periods.span(repo_config.period("night")) == (1080, 1440)  # 00:00-06:00
    assert periods.span(repo_config.period("evening")) == (720, 1080)  # 18:00-00:00


def test_footer_pages_must_exist(tmp_path: Path) -> None:
    config_dir = tiny_config_dir(tmp_path)
    pages = (config_dir / "pages.yaml").read_text(encoding="utf-8")
    assert "pages: [about, guide, status, legal, privacy]" in pages
    pages = pages.replace("pages: [about, guide, status, legal, privacy]", "pages: [about, nope]")
    (config_dir / "pages.yaml").write_text(pages, encoding="utf-8")
    with pytest.raises(ConfigError, match="footer references unknown page 'nope'"):
        load_config(config_dir)


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        ('start: "12:00"\n    end: "14:00"', 'start: "12:00"\n    end: "13:00"', "leaves a gap"),
        ('start: "14:00"\n    end: "18:00"', 'start: "13:00"\n    end: "18:00"', "overlaps"),
        (
            "      - { fr: demain soir, en: tomorrow evening, es: mañana por la tarde }\n",
            "",
            "needs 2 labels",
        ),
    ],
)
def test_time_slots_must_tile_the_day(tmp_path: Path, old: str, new: str, message: str) -> None:
    config_dir = tiny_config_dir(tmp_path)
    _edit(config_dir, "periods.yaml", old, new)
    with pytest.raises(ConfigError, match=message):
        load_config(config_dir)


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        ("        block: data_sources\n", "", "needs paragraphs, links or a block"),
        ("  repository: https://", "  repository: http://", "String should match"),
        ("  - id: legal\n", "  - id: about\n", "duplicate page id 'about'"),
    ],
)
def test_invalid_pages_are_rejected(tmp_path: Path, old: str, new: str, message: str) -> None:
    config_dir = tiny_config_dir(tmp_path)
    pages = (config_dir / "pages.yaml").read_text(encoding="utf-8")
    assert old in pages
    (config_dir / "pages.yaml").write_text(pages.replace(old, new, 1), encoding="utf-8")
    with pytest.raises(ConfigError, match=message):
        load_config(config_dir)


def test_kpi_and_tile_periods_must_exist(tmp_path: Path) -> None:
    config_dir = tiny_config_dir(tmp_path)
    _edit(
        config_dir, "kpis.yaml", "periods: [day, morning, midday, afternoon]", "periods: [brunch]"
    )
    with pytest.raises(ConfigError, match="unknown period 'brunch'"):
        load_config(config_dir)


def test_tile_titles_cannot_use_the_period_placeholder(tmp_path: Path) -> None:
    config_dir = tiny_config_dir(tmp_path)
    _edit(config_dir, "tiles.yaml", "en: Snow,", 'en: "Snow {period}",')
    with pytest.raises(ConfigError, match=r"title \(en\) cannot use '\{period\}'"):
        load_config(config_dir)


def test_periods_need_a_day_badge_per_day(tmp_path: Path) -> None:
    config_dir = tiny_config_dir(tmp_path)
    _edit(
        config_dir,
        "periods.yaml",
        "  - { tone: tomorrow, label: { fr: Dem., en: Tmrw, es: Mañana } }\n",
        "",
    )
    with pytest.raises(ConfigError, match="`badge_days` needs 2 labels"):
        load_config(config_dir)


def test_a_period_badge_needs_a_tone(tmp_path: Path) -> None:
    config_dir = tiny_config_dir(tmp_path)
    _edit(config_dir, "periods.yaml", "    tone: midday\n", "")
    with pytest.raises(ConfigError, match="period 'midday' needs a `tone`"):
        load_config(config_dir)


def test_repository_periods_have_short_time_badges(repo_config: Config) -> None:
    periods = repo_config.periods
    assert [d.tone for d in periods.badge_days] == ["today", "tomorrow"]
    assert periods.badge_tonight is not None
    assert repo_config.period("day").badge is None  # whole day: the day alone
    assert repo_config.period("sunset").tone == "evening"
    assert repo_config.period("overnight").tone == "night"
    for period in periods.periods:
        if period.badge is not None:
            assert len(period.badge.fr) <= 6, period.id


def test_tile_periods_default_to_those_of_its_kpis(repo_config: Config) -> None:
    tiles = {t.id: t for t in repo_config.tiles}
    assert repo_config.tile_periods(tiles["onpiste_powder"]) == [
        "day",
        "morning",
        "midday",
        "afternoon",
    ]
    assert repo_config.tile_periods(tiles["snowfall_today"])[0] == "day"


@pytest.mark.parametrize(
    ("file", "old", "new", "message"),
    [
        (
            "rewinds.yaml",
            "      - season_total_snowfall\n",
            "      - snowfall_chance\n",
            "KPI 'snowfall_chance' is not historical",
        ),
        (
            "filters.yaml",
            "    theme: rewind\n",
            "    theme: rewind\n    levels: [day]\n",
            "filter 'rewind-2025-26' cannot have levels",
        ),
        ("rewinds.yaml", "    end: 2026-05-01", "    end: 2025-11-01", "end must be after start"),
        ("kpis.yaml", "    value: { unit: h, decimals: 0 }\n", "", "needs `value`"),
    ],
)
def test_invalid_rewinds_are_rejected(
    tmp_path: Path, file: str, old: str, new: str, message: str
) -> None:
    config_dir = tiny_config_dir(tmp_path)
    text = (config_dir / file).read_text(encoding="utf-8")
    assert old in text
    (config_dir / file).write_text(text.replace(old, new, 1), encoding="utf-8")
    with pytest.raises(ConfigError, match=message):
        load_config(config_dir)


def test_historical_kpis_need_a_season_aggregator(tmp_path: Path) -> None:
    config_dir = tiny_config_dir(tmp_path)
    kpis = (config_dir / "kpis.yaml").read_text(encoding="utf-8")
    kpis = kpis.replace("aggregator: season_total_snowfall", "aggregator: snowfall_chance", 1)
    (config_dir / "kpis.yaml").write_text(kpis, encoding="utf-8")
    errors = plugin_errors(load_config(config_dir))
    assert any("is historical but aggregator 'snowfall_chance'" in e for e in errors)


def test_kpi_descriptions_have_no_placeholders(tmp_path: Path) -> None:
    config_dir = tiny_config_dir(tmp_path)
    kpis = (config_dir / "kpis.yaml").read_text(encoding="utf-8")
    kpis = kpis.replace(
        "le manteau neigeux dépasse 70 cm", "le manteau neigeux dépasse {threshold_cm} cm", 1
    )
    (config_dir / "kpis.yaml").write_text(kpis, encoding="utf-8")
    with pytest.raises(ConfigError, match=r"description \(fr\) has a placeholder"):
        load_config(config_dir)


def test_service_status_page_is_linked_from_the_footer(repo_config: Config) -> None:
    pages = {p.id: p for p in repo_config.pages.pages}
    assert "status" in repo_config.pages.footer.pages
    blocks = [s.block for s in pages["status"].sections if s.block]
    assert blocks == [
        "service_summary",
        "service_sources",
        "service_transforms",
        "service_kpis",
        "service_tiles",
    ]


def test_tile_guide_page_explains_every_mark(repo_config: Config) -> None:
    pages = {p.id: p for p in repo_config.pages.pages}
    assert "guide" in repo_config.pages.footer.pages
    sections = {s.id: s for s in pages["guide"].sections}
    assert [s.block for s in pages["guide"].sections if s.block] == [
        "tile_front",
        "time_badges",
        "tile_back",
    ]
    # One numbered paragraph per mark drawn by web/src/components/TileGuide.svelte.
    for section_id, marks in (("front-marks", 8), ("back-marks", 9)):
        numbers = [p.fr.split(".")[0] for p in sections[section_id].paragraphs]
        assert numbers == [str(n) for n in range(1, marks + 1)]


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        (
            "range: [snow_cm_p10, snow_cm_p90], tolerance: 3 }",
            "range: [snow_cm_p10, snow_cm_p90] }",
            "needs `driver`, `range` and `tolerance`",
        ),
        (
            "driver: snow_cm_p50, range: [snow_cm_p10, snow_cm_p90], tolerance: 3",
            "driver: snow_cm_p75, range: [snow_cm_p10, snow_cm_p90], tolerance: 3",
            "display driver 'snow_cm_p75' is not in `drivers`",
        ),
        (
            '        - { min: 0, label: { fr: Non, en: "No", es: "No" } }\n',
            '        - { min: 0.1, label: { fr: Non, en: "No", es: "No" } }\n',
            "the last at 0",
        ),
        (
            "        - { max: -48, label:"
            " { fr: risque grave, en: severe risk, es: riesgo severo } }\n",
            "        - { max: -60, label:"
            " { fr: risque grave, en: severe risk, es: riesgo severo } }\n",
            "increasing `max`",
        ),
    ],
)
def test_invalid_kpi_displays_are_rejected(
    tmp_path: Path, old: str, new: str, message: str
) -> None:
    config_dir = tiny_config_dir(tmp_path)
    text = (config_dir / "kpis.yaml").read_text(encoding="utf-8")
    assert old in text
    (config_dir / "kpis.yaml").write_text(text.replace(old, new, 1), encoding="utf-8")
    with pytest.raises(ConfigError, match=message):
        load_config(config_dir)


def test_value_displays_rank_by_value_and_rate_the_spread() -> None:
    from bluebird_pipeline.gold.base import spread_confidence

    assert spread_confidence(1.0, 3.5, 3, 91) == "high"
    assert spread_confidence(1.0, 6.0, 3, 91) == "medium"
    assert spread_confidence(0.0, 9.0, 3, 91) == "low"
    assert spread_confidence(1.0, 2.0, 3, 5) == "low"  # too few scenarios
    assert spread_confidence(None, 2.0, 3, 91) == "low"


WEBCAM = (
    "    webcams:\n"
    "      - { id: top, name: Top, position: summit, provider: skaping,"
    ' url: "https://www.skaping.com/alpha/top" }\n'
)


def test_station_webcams_are_read(tmp_path: Path) -> None:
    stations = TWO_STATIONS.replace(
        "    elevation: { base: 1500, summit: 2500 }\n",
        "    elevation: { base: 1500, summit: 2500 }\n" + WEBCAM,
    )
    config = load_config(tiny_config_dir(tmp_path, stations))
    alpha = config.stations["pyrenees"].stations[0]
    assert [(w.id, w.position, w.provider) for w in alpha.webcams] == [("top", "summit", "skaping")]


@pytest.mark.parametrize(
    ("webcam", "message"),
    [
        (WEBCAM.replace("position: summit", "position: roof"), "Input should be 'summit'"),
        (WEBCAM.replace('"https://', '"http://'), "String should match"),
        (WEBCAM.replace("provider: skaping", "provider: viewsurf"), "Input should be 'skaping'"),
        (WEBCAM + WEBCAM.replace("    webcams:\n", ""), "duplicate webcam id"),
    ],
)
def test_invalid_webcams_are_rejected(tmp_path: Path, webcam: str, message: str) -> None:
    anchor = "    elevation: { base: 1500, summit: 2500 }\n"
    stations = TWO_STATIONS.replace(anchor, anchor + webcam)
    with pytest.raises(ConfigError, match=message):
        load_config(tiny_config_dir(tmp_path, stations))


def test_tiles_are_classified_by_scope_format_and_visual(repo_config: Config) -> None:
    tiles = {t.id: t for t in repo_config.tiles}
    assert {t.scope for t in tiles.values()} == {"ranking"}
    assert {t.format for t in tiles.values()} == {"full", "banner", "compact"}
    assert tiles["offpiste_powder"].visual == "scene"  # default, compact tiles have no image
    assert tiles["bluebird_day"].visual == "photo"
    rule = tiles["bluebird_day"].webcam
    assert rule is not None and rule.positions == ["summit"] and rule.min_probability == 0.6
    assert [t.id for t in tiles.values() if t.webcam] == ["bluebird_day"]


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        ("    format: compact\n", "    format: ranking\n", "Input should be 'full'"),
        ("    format: compact\n", "    format: compact\n    visual: photo\n", "has no image"),
        (
            "    format: compact\n",
            "    format: compact\n    webcam: { positions: [summit] }\n",
            "has no image",
        ),
        ("      scene: piste\n", "      scene: piste\n      photo: leader\n", "visual: photo"),
        ("    scope: ranking\n", "    scope: station\n", "Input should be 'ranking'"),
        (
            "    kpis: [season_total_snowfall]\n",
            "    kpis: [season_total_snowfall]\n    webcam: { positions: [summit] }\n",
            "cannot link a webcam",
        ),
        (
            "    webcam: { positions: [summit], min_probability: 0.6 }\n",
            "    webcam: { positions: [] }\n",
            "at least 1 item",
        ),
    ],
)
def test_invalid_tile_axes_are_rejected(tmp_path: Path, old: str, new: str, message: str) -> None:
    config_dir = tiny_config_dir(tmp_path)
    if old == "    scope: ranking\n":
        _edit(
            config_dir,
            "tiles.yaml",
            "    format: compact\n",
            "    scope: ranking\n    format: compact\n",
        )
    _edit(config_dir, "tiles.yaml", old, new)
    with pytest.raises(ConfigError, match=message):
        load_config(config_dir)
