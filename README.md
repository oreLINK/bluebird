# Bluebird

Bluebird is a static, mobile-first website that publishes, every 6 hours,
the probability of good ski conditions in French ski resorts, computed from
ensemble weather forecasts. It starts with the Pyrenees and three KPIs:

| KPI | Question it answers |
|---|---|
| `snowfall_chance` | Will it snow during this time slot (or the whole ski day)? |
| `onpiste_powder_chance` | Will fresh snow cover the pistes after grooming? |
| `offpiste_powder_chance` | Will there be fresh, unspoilt powder off-piste? |

Each KPI is computed for several **periods** of today and tomorrow (this
morning, lunchtime, this afternoon, this evening, tonight, the whole day…, see
`config/periods.yaml`). Each KPI and period is a tile that ranks the resorts
of the selected mountain range by probability, like a sports-betting page;
a tile disappears when its period is over. The footer shows the state of
every data source, transformation, KPI and tile after the last refresh. The
UI is in French or English.

These are **live** KPIs. **Rewinds** add **historical** KPIs: the review of a
closed season, built once from archived forecasts. The first one, *Rewind
25/26* (1 December 2025 – 1 May 2026, Pyrenees), ranks the resorts on season
snowfall at the resort, on the slopes and off-piste around them, on the
longest snowfall and on the share of days with more than 70 cm of snow on the
slopes. It has its own red filter, right after "All".

This README is for developers. See [PROJECT.md](PROJECT.md) for the product
view, [CONTEXT.md](CONTEXT.md) for the AI-assistant briefing and
[AGENTS.md](AGENTS.md) for the rules AI agents follow on every prompt.

---

## Contents

1. [Architecture](#architecture)
2. [Repository layout](#repository-layout)
3. [Getting started](#getting-started)
4. [Commands](#commands)
5. [Data layers and file formats](#data-layers-and-file-formats)
6. [Configuration reference](#configuration-reference)
7. [Extending Bluebird](#extending-bluebird)
8. [Frontend](#frontend)
9. [Testing and quality](#testing-and-quality)
10. [Git workflow and deployment](#git-workflow-and-deployment)
11. [Data sources, limits and licences](#data-sources-limits-and-licences)
12. [Troubleshooting](#troubleshooting)

---

## Architecture

```
                       config/*.yaml  (massifs, stations, KPIs, tiles, layout, sources)
                              │
          ┌───────────────────┴─────────────────────────────┐
          ▼                                                 ▼
  pipeline/ (Python)                                  web/ (Svelte + Vite)
  ┌───────────────┐   ┌───────────────┐                bundles the YAML at build time
  │ bronze/       │   │ silver/       │                fetches diamond JSON at runtime
  │ Extractor*    │──▶│ Transformer*  │
  │ raw .json.gz  │   │ tidy .parquet │
  └───────────────┘   └──────┬────────┘
                             ▼
  ┌───────────────┐   ┌───────────────┐
  │ diamond/      │◀──│ gold/         │
  │ Displayer*    │   │ Aggregator*   │
  │ site .json    │   │ KPIs .parquet │
  └──────┬────────┘   └───────────────┘
         │  GitHub Actions (refresh.yml, every 6 h): one job per source,
         │  dataset, KPI and massif, then a status job; publishes
         │  gold + diamond + status.json
         ▼
  gh-pages branch ──▶ GitHub Pages ──▶ smartphone
```

- **Static site.** No server, no database. The pipeline writes JSON files and
  the site reads them.
- **Medallion layers.** Each layer is a Python sub-package with one abstract
  base class and one plugin file per implementation. A plugin registers
  itself with a decorator, so adding a source or a KPI means adding a file.
- **Configuration first.** Massifs, stations, KPI parameters and labels,
  tiles and their order live in YAML. Changing them needs no code change.
- **One contract.** The diamond JSON shape is defined once as pydantic
  models, exported as JSON Schema, and turned into TypeScript types. CI fails
  when the two sides drift.
- **Few API calls.** Each source is fetched with one grouped request per
  refresh (every station and elevation band at once), four times a day.

## Repository layout

```
bluebird/
├── README.md                  # developers (this file)
├── PROJECT.md                 # site users: purpose, features, roadmap, limits
├── CONTEXT.md                 # AI agents: architecture, invariants, recipes, pitfalls
├── AGENTS.md                  # AI agents: mandatory rules for every prompt
├── CLAUDE.md                  # imports AGENTS.md + CONTEXT.md for Claude Code
├── config/                    # human-edited configuration (single source of truth)
│   ├── massifs.yaml
│   ├── stations/<massif>.yaml
│   ├── kpis.yaml
│   ├── filters.yaml
│   ├── tiles.yaml
│   ├── layout.yaml
│   ├── sources.yaml
│   ├── periods.yaml           # time slots of the ski day (morning, evening…) and their labels
│   ├── pages.yaml             # footer + full-window pages (about, service status, legal notice, privacy)
│   ├── rewinds.yaml           # Rewinds: closed seasons and their historical KPIs
│   ├── reference/<dataset>/<massif>.geojson  # fetched once a season (`bluebird reference`)
│   ├── rewind/<id>/<massif>.hourly.parquet, .json  # GENERATED by `bluebird rewind`, committed
│   └── schemas/*.schema.json  # GENERATED by `bluebird schemas`
├── pipeline/                  # Python package `bluebird_pipeline`
│   ├── pyproject.toml  uv.lock  .python-version
│   ├── src/bluebird_pipeline/
│   │   ├── cli.py             # `bluebird` command
│   │   ├── config.py          # pydantic models of every YAML file + cross-checks
│   │   ├── registry.py        # plugin registry + autodiscovery
│   │   ├── context.py         # RunContext: config, storage, dates, silver access
│   │   ├── runner.py          # runs the layers in order, isolates failures, gold fallback
│   │   ├── report.py          # step reports (ok / partial / stale / down) of each unit
│   │   ├── checks.py          # config ↔ plugin consistency checks
│   │   ├── schemas.py         # JSON Schema export
│   │   ├── reference.py       # reference data: refresh, committed files, loading
│   │   ├── rewind.py          # Rewinds: season archive, historical KPIs, committed files
│   │   ├── geo.py             # distances and offsets on [lon, lat] points
│   │   ├── demo.py            # synthetic demo data for the frontend
│   │   ├── storage/           # Storage interface, LocalStorage, key conventions
│   │   ├── bronze/            # base.py + extractor_*.py
│   │   ├── silver/            # base.py + transformer_*.py
│   │   ├── gold/              # base.py + aggregator_*.py
│   │   └── diamond/           # base.py + models.py + displayer_*.py + _status.py (status.json)
│   └── tests/                 # mirrors the layer folders
├── web/                       # Vite + Svelte 5 + TypeScript
│   ├── src/
│   │   ├── App.svelte  main.ts
│   │   ├── lib/               # config, data loading, periods, status, i18n, formatting
│   │   │   └── generated/     # GENERATED TypeScript types (npm run gen:types)
│   │   ├── tiles/             # registry, tileModel, TileBanner, TileBannerFull, TileSimple, TileRanking, OddsRow…
│   │   ├── components/        # Logo, AppHeader, AppMenu, FilterBar, ConfidenceDots, BannerArt…
│   │   ├── assets/photos/     # banner photos + credits.yaml (see its README)
│   │   └── styles/            # tokens.css, glass.css, base.css
│   └── public/data/diamond/   # demo data for local development only
├── scripts/
│   ├── setup-github.sh        # one-time GitHub setup (run manually)
│   ├── ci/publish-gh-pages.sh # used by workflows to write gh-pages
│   └── ci/fetch-gh-pages-data.sh # restores published gold/diamond (read-only)
└── .github/
    ├── actions/setup-pipeline/ # composite action: uv + pipeline install
    └── workflows/             # ci.yml, deploy.yml, refresh.yml, reference.yml, rewind.yml, guard-gh-pages.yml
```

## Getting started

### Prerequisites

- [uv](https://docs.astral.sh/uv/) (installs Python 3.12 automatically)
- Node.js 22 and npm
- [GitHub CLI](https://cli.github.com/) only for the one-time GitHub setup

> **iCloud Drive / Dropbox warning.** Do not keep the Python virtualenv inside
> a synced folder. iCloud flags files in `.venv` as hidden, and Python 3.13+
> silently ignores hidden `.pth` files, which breaks the editable install
> (`ModuleNotFoundError: bluebird_pipeline`). Either clone the repository
> outside iCloud, or point uv to another folder:
> `export UV_PROJECT_ENVIRONMENT="$HOME/.venvs/bluebird"`.
> `node_modules` also syncs thousands of files; prefer a non-synced clone.

### Pipeline

```bash
cd pipeline
uv sync                      # create the environment
uv run bluebird validate     # check config/ and plugins
uv run bluebird run          # fetch live data, write data/{bronze,silver,gold,diamond}
uv run pytest                # tests (no network)
```

The live run takes a few seconds: one grouped request per source. Output goes
to `<repo>/data/` (git-ignored).

### Website

```bash
cd web
npm ci
npm run dev                  # http://localhost:5173, uses web/public/data demo files
```

To see your own pipeline output in the site, copy it over the demo files:
`cp -R ../data/diamond public/data/` (do not commit the result; regenerate
the demo with `uv run bluebird demo`).

## Commands

### Pipeline (`cd pipeline`)

| Command | What it does |
|---|---|
| `uv run bluebird validate` | Validate every YAML file, cross-references and plugin parameters. |
| `uv run bluebird run` | Run all layers for the current ski day (Paris time; it starts at 06:00) on daily sources, then write `diamond/status.json` and the manifest. |
| `uv run bluebird run --layer gold` | Run one layer (`bronze`, `silver`, `gold`, `diamond`). |
| `uv run bluebird run --date 2026-12-14 --layer gold` | Recompute a stored ski day. Live APIs always return the current forecast, so only use `--date` with `silver`, `gold` or `diamond` on data already in storage. |
| `uv run bluebird run --massif pyrenees` | Restrict to one massif (repeatable). |
| `uv run bluebird run --source open_meteo_forecast` | Run selected daily or `on_demand` sources only. |
| `uv run bluebird run --layer gold --kpi snowfall_chance` | Compute only these KPIs (repeatable), as one CI job per KPI does. |
| `uv run bluebird run --run-id 20261214T050700Z` | Pin the run start: every CI job of a refresh shares the id chosen by `plan`. Refused with the bronze layer when older than 3 hours. |
| `uv run bluebird run --report r.json --export out/` | Write the step report (JSON) and copy the files written to `out/` (CI artifacts). |
| `uv run bluebird plan [--json]` | List the units of a refresh: run id, ski day, sources, silver datasets, KPIs, massifs (the CI matrices). |
| `uv run bluebird status --reports DIR [--run-id ID] [--summary FILE]` | Write `diamond/status.json` and the manifest from step reports and stored data; append a Markdown summary. |
| `uv run bluebird reference` | Fetch reference sources (pistes, lifts) and rewrite `config/reference/`. Options: `--massif`, `--source`, `--no-fetch` (rebuild from the last stored bronze). |
| `uv run bluebird rewind --rewind 2025-26` | Build a Rewind once its season is over: fetch the season archive, write `config/rewind/<id>/` (hourly Parquet + rankings JSON). Options: `--massif`, `--data-dir`, `--source <id>` (fetch only this season source; its rows replace the previous ones of its model, the other sources' rows are kept), `--no-fetch` (recompute the KPIs from the committed hourly files, no API call). Refuses a season that is not over. |
| `uv run bluebird run --data-dir /tmp/x` | Use another storage root (also `BLUEBIRD_DATA_DIR`). |
| `uv run bluebird run --strict` | Exit non-zero on any error (default: only if nothing was produced). |
| `uv run bluebird schemas [--check]` | Regenerate (or verify) `config/schemas/*.schema.json`. |
| `uv run bluebird plugins` | List registered extractors, transformers, aggregators, displayers. |
| `uv run bluebird demo [--now 2027-01-15T17:07+00:00]` | Rebuild `web/public/data/diamond` (payload, status, manifest) from synthetic weather, as the 06:00 refresh (or the refresh at `--now`). |
| `uv run ruff format . && uv run ruff check .` | Format and lint. |

### Website (`cd web`)

| Command | What it does |
|---|---|
| `npm run dev` | Development server with hot reload. |
| `npm run build` / `npm run preview` | Production build in `web/dist` / serve it locally. |
| `npm run check` | Type-check Svelte and TypeScript (`svelte-check`). |
| `npm test` | Unit tests (Vitest). |
| `npm run gen:types` | Regenerate `src/lib/generated/*.ts` from `config/schemas`. |

## Data layers and file formats

| Layer | Produced by | Content | Format | Key (relative to the storage root) |
|---|---|---|---|---|
| Bronze | `Extractor*` | Raw responses, unchanged, with request metadata | gzip JSON | `bronze/{source}/{date}/{run_id}.json.gz` |
| Silver | `Transformer*` | Tidy, typed rows with canonical units | Parquet (zstd) | `silver/{dataset}/date={date}/{run_id}.parquet` |
| Gold | `Aggregator*` | One row per station × period, one file per KPI | Parquet | `gold/kpis/date={ski_day}/{kpi_id}.parquet` |
| Diamond | `Displayer*` + status step | Frontend payloads (rankings per period), service status | Minified JSON | `diamond/{massif}/latest.json`, `diamond/{massif}/{ski_day}.json`, `diamond/manifest.json`, `diamond/status.json` |
| Configuration | humans | Massifs, stations, KPIs, tiles, layout, sources | YAML (+ JSON Schema) | `config/*.yaml` |
| Reference | `Transformer*` of `schedule: reference` sources | Slow-changing facts: pistes and lifts with geometry | GeoJSON | `config/reference/{dataset}/{massif}.geojson` (committed) |
| Season archive (Rewind) | `Transformer*` of `schedule: season` sources | A closed season, hour by hour, per station and sampling point | Parquet (zstd, float32) | `config/rewind/{id}/{massif}.hourly.parquet` (committed) |
| Rewind gold / payload | `SeasonAggregator*` / `DisplayerRewind` | Historical KPI values; ranked payload for the site | Parquet / JSON | `gold/rewind/{id}/kpis.parquet` (data folder); `config/rewind/{id}/{massif}.json` (committed, bundled by the site) |

Why these formats:

- **JSON (gzip) for bronze**: keeps API responses byte-for-byte meaningful,
  so any later layer can be rebuilt without calling the API again.
- **Parquet for silver and gold**: typed, columnar and compressed; readable by
  polars, pandas or DuckDB (`duckdb -c "select * from 'gold/**/*.parquet'"`).
- **JSON for diamond**: the browser reads it directly (≈120 KB per massif
  with 24 KPI periods, ≈15 KB gzipped by Pages).
- **YAML for configuration**: comfortable to edit, validated by strict schemas.
- **GeoJSON for reference geography**: standard, readable by any GIS tool,
  and rendered as a map by GitHub, which makes refresh pull requests easy to review.

### Daily data vs reference data

Station facts never come from an API call at run time:

- **Hand-written facts** (position, elevations, aspects, grooming and opening
  times) live in `config/stations/<massif>.yaml`.
- **Fetched facts** that barely change (pistes and lifts from OpenStreetMap)
  come from sources with `schedule: reference`. They are fetched once a season
  by `bluebird reference` (or the *Refresh reference data* workflow), written
  to `config/reference/`, committed and reviewed in a pull request. Every run
  reads them with `RunContext.reference(dataset)`, whatever the date, without
  calling the source again. A failed refresh never overwrites an existing file.
- **Daily data** (weather) is fetched by every refresh (every 6 hours) and
  stored by ski day.
- **Season archives** (Rewinds, `config/rewinds.yaml`) come from sources with
  `schedule: season`, fetched once *after* a season is over by `bluebird
  rewind` (or the *Build a Rewind* workflow). The hourly table of the season
  and the ranked payload are written to `config/rewind/<id>/`, committed and
  reviewed in a pull request. The historical KPIs read the committed hourly
  file, so they can be recomputed or extended (`--no-fetch`) without calling
  the source again. The daily run never fetches or computes them.

`bluebird validate` warns when a reference or Rewind file is missing, and a
test fails if a station has no piste or lift in it.

**White days.** `gold/_whiteout.py` holds the rule shared by the live
`whiteout_chance` KPI (ensemble scenarios, computed for the whole-day
period of today and tomorrow only) and the historical `season_white_days` KPI (AROME archive,
domain points): an hour of the ski day is white when the point is in the
cloud (humidity ≥ `rh_min_pct` and low cloud ≥ `low_cloud_min_pct`, total
cloud for ICON members, which lack low cloud), under ≥ `snowfall_min_cm_h`
of snow, or in flat light (global radiation below `clear_sky_index_max` ×
the clear-sky radiation from the sun position, Haurwitz model); a day is
white from `min_white_hours` white hours. All thresholds are KPI `params`.
The ensemble source fetches today and tomorrow (`forecast_days: 2`) with
humidity, cloud cover, low cloud and radiation for this.

**Rewind sampling.** For each station the season source asks for the station
point (mid elevation, like the live KPIs), `domain_points` points spread at
equal distances along its OSM pistes and `offpiste_points` points on a ring
around them (centre of the pistes, farthest piste + `offpiste_margin_m`).
Domain and off-piste points carry no elevation, so Open-Meteo uses its terrain
model. Several season sources can feed the same hourly file, one model each
(`open_meteo_historical`: AROME snowfall, sunshine, cloud cover, weather code
at station, domain and off-piste points; `open_meteo_historical_snowpack`:
ICON snow depth at station and domain points); rows are keyed by `model`, and
a variable a model was not asked for is null in its rows. Rows are keyed by
station, point, model and hour, and each source owns the columns of its
variables: `rewind.merge_columns` replaces only those, so two sources of the
same model (AROME snow and AROME light) share rows. Adding a variable later is
a new source plus `bluebird rewind --source <id>`, without re-fetching the
others. Points are deterministic (`bronze/_season_points.py`) and stored with
every hourly row. A station without pistes only gets its own point (no
domain or off-piste value).

`run_id` is a UTC timestamp (`20261214T053000Z`). Silver keeps every run;
gold and diamond keep one object per ski day (the last run of the day wins).
Gold files written before periods existed (`kpis.parquet`) stay in the
history but are ignored by the pipeline.

### Ski days and periods

- A **ski day** runs from 06:00 local time to 06:00 the next day
  (`day_start` in `config/periods.yaml`). The refresh at 00:00 still belongs to
  the previous ski day, so "tonight" keeps its meaning after midnight. The
  ski day of a run is its `run_date` (`RunContext.create`).
- **Periods** are defined in `config/periods.yaml`: time slots that must
  cover the ski day exactly once (night 00–06, morning 06–12, midday 12–14,
  afternoon 14–18, evening 18–00), plus `day` with `native_window: true` (the
  KPI uses its own window, e.g. 08:00–17:00, and the period is shown from
  06:00 to 18:00). Each period has one label per day of the horizon
  (`horizon_days: 2`: today and tomorrow).
- Each KPI lists its `periods` in `kpis.yaml`. Its aggregator implements
  `compute(ctx, station, period)`; the base class loops over every station and
  every period **not over yet** at the run time (`ctx.period_instances()`).
  A period instance has a stable key, `period_id@ski_day`.
- Snowfall uses the slot itself as its window. Powder KPIs evaluate the slot
  at its start, never before lifts open (so the morning slot means "at
  opening").

### Fallback and service status

- **Fallback.** Before computing a KPI, CI restores the data already
  published on `gh-pages` (`scripts/ci/fetch-gh-pages-data.sh`). If a KPI
  cannot be recomputed (source down, error), `run_gold_kpi` keeps the rows of
  the latest run that computed each period still to come
  (`gold.base.read_gold`), with their original `generated_at`. The site shows
  them with a "data from 06:00" badge.
- **Step reports.** Every unit records a `StepReport` (`report.py`): `ok`,
  `partial` (some stations missing), `stale` (values from an earlier run) or
  `down`. In CI each job writes its report with `--report`.
- **Status.** `diamond/_status.py` builds `diamond/status.json`: sources and
  transformations from the reports (a missing report counts as `down`), KPI
  periods from the gold data, and tiles from the published massif payloads
  (what visitors see). The site footer displays it; the CI job summary lists
  the same with error messages.

**Canonical silver units**: time in UTC (`time_utc`), heights in m,
temperature in °C, precipitation in mm, snowfall in cm, wind in km/h. The
Open-Meteo transformer checks the units of every response.

### Where data is stored in production

Everything lives on GitHub; there is no external storage.

| Layer | Location | Retention |
|---|---|---|
| Bronze, silver | Runner disk, then a workflow artifact | 7 days |
| Gold | `gh-pages` branch, `data/gold/` | Unlimited (KPI history) |
| Diamond | `gh-pages` branch, `data/diamond/`, served by Pages | Unlimited (`latest.json` + dated archive) |
| Reference (pistes, lifts) | `config/reference/` on `main`, via pull request | Until the next refresh; history in git |
| Rewind (season hourly + rankings) | `config/rewind/` on `main`, via pull request | Permanent (a closed season does not change) |

`main` contains code and configuration, including reference data.
Nothing under `/data` is ever committed there. The storage interface (`pipeline/src/bluebird_pipeline/storage/`) can
gain a cloud backend later without touching the layers.

## Configuration reference

All files start with a `yaml-language-server` header, so VS Code (with the
Red Hat YAML extension) validates and autocompletes them from `config/schemas/`.

| File | Purpose | Key fields |
|---|---|---|
| `massifs.yaml` | Mountain ranges of the massif bar | `id`, `name {fr,en}`, `timezone`, `enabled`, `order`, `bbox`, `skyline` |
| `stations/<massif>.yaml` | Resorts of one massif | `defaults {grooming_end, lifts_open}`, `stations[]`: `id`, `name`, `short_name?` (≤ 20 chars, shown in tiles), `lat`, `lon`, `elevation {base, summit, mid?}`, `aspects`, `grooming_end?`, `lifts_open?`, `website?`, `enabled` |
| `kpis.yaml` | KPI registry | `id`, `aggregator`, `kind` (`live` / `historical`), `order` (`desc` / `asc`: lowest value first, e.g. fewest white days), `value {unit, unit_label, unit_label_one, decimals, scale, max}` (`unit_label {fr,en}` when the unit depends on the language, e.g. jours / days, and `unit_label_one` its singular, chosen with the language's plural rules) (historical; `scale` converts the aggregator's unit, e.g. `0.01` for cm → m; `max` is the value of a full bar, e.g. `100` for a percentage, default the best value), `name`, `description`, `method?` (`{param}` placeholders, shown on the tile back), `params`, `drivers {key: {label, unit, decimals}}`, `filters[]`, `periods[]` (live KPIs; default `[day]`), `enabled` |
| `periods.yaml` | Time slots of the ski day | `day_start`, `horizon_days`, `periods[]`: `id`, `start`, `end`, `native_window?`, `labels[]` (`{fr,en}` per day: today, tomorrow) |
| `filters.yaml` | Filter bar chips, in order | `id`, `name {fr,en}`, `icon?`, `all?` (every tile but exclusive ones), `exclusive?` (its tiles only show under it), `theme?` (`default` / `rewind`) |
| `tiles.yaml` | KPI containers; a live tile is shown once per period | `id`, `type`, `kpis[]`, `title?` (live: must contain `{period}`; Rewind: must not), `periods?[]` (live), `icon?`, `options` (`details` turns station details on, off by default) |
| `layout.yaml` | Tile order | `default[]`, `overrides {massif: [tiles]}` |
| `sources.yaml` | Data sources | `id`, `extractor`, `transformer`, `schedule (daily/on_demand/reference/season)`, `params`, `attribution` |
| `rewinds.yaml` | Rewinds (closed seasons) | `id` (e.g. `2025-26`), `name`, `start`, `end` (local days, included), `massifs[]`, `kpis[]` (historical), `filter` (exclusive) |
| `pages.yaml` | Footer and full-window pages | `footer {repository, pages[]}`, `pages[]`: `id` (URL hash), `title`, `sections[]`: `id`, `title`, `paragraphs[]`, `links[] {label, url}`, `block?` (`data_sources` / `photo_credits` / `service_summary` / `service_sources` / `service_transforms` / `service_kpis` / `service_tiles`) |

Validation is strict: unknown keys, wrong types, duplicate ids, dangling
references (tile → KPI, layout → tile, KPI → aggregator, KPI → period,
source → extractor), time slots with gaps or overlaps, tile titles without
`{period}`,
invalid plugin parameters and KPIs whose silver dataset no source produces
are all errors. Run `uv run bluebird validate` after every edit.

Station times are local wall-clock times (`HH:MM`) in the massif timezone.
A `grooming_end` later than `lifts_open` (e.g. `22:00`) means the previous
evening.

## Extending Bluebird

Every extension point is a file plus, usually, a YAML entry. Naming
convention: the class prefix says the layer, and the file is the snake_case
of the class (`ExtractorOpenMeteoEnsemble` → `bronze/extractor_open_meteo_ensemble.py`).
A test enforces it.

### Add a station

1. Add a block to `config/stations/<massif>.yaml` (coordinates at the middle
   of the ski area: they select the weather model grid cell).
2. Give it a `short_name` (≤ 20 characters) for the tiles.
3. Create its photo folder `web/src/assets/photos/<massif>/<station_id>/`
   (with a `.gitkeep` until it has a photo; a test checks the folder exists).
4. `uv run bluebird reference --massif <massif>` to add its pistes and lifts.
5. `uv run bluebird validate`.

The next refresh includes it; no frontend change is needed.

### Add a massif

1. Add an entry to `config/massifs.yaml` (`id`, `name`, `timezone`, `bbox`,
   optional `skyline` for the ridges of the banner illustrations).
2. Create `config/stations/<id>.yaml`.
3. Optionally add a `layout.yaml` override for its tile order.
4. `uv run bluebird reference --massif <id>` to fetch its pistes and lifts.
5. `uv run bluebird validate`, then `uv run bluebird demo` if you want demo data.

The massif appears in the massif bar after the next deploy and gets data after
the next refresh (its CI jobs come from `bluebird plan`, nothing to change in
the workflow).

### Add a data source (API or scraper)

1. **Bronze**: create `pipeline/src/bluebird_pipeline/bronze/extractor_<name>.py`:

   ```python
   from typing import ClassVar
   from ..context import RunContext
   from .base import BronzeRecord, Extractor, ExtractorParams, register_extractor

   class MyParams(ExtractorParams):
       base_url: str = "https://api.example.com/v1/snow"

   @register_extractor("my_source")
   class ExtractorMySource(Extractor):
       Params: ClassVar[type[ExtractorParams]] = MyParams
       params: MyParams

       def extract(self, ctx: RunContext) -> list[BronzeRecord]:
           return [
               self.get_json(self.params.base_url, {"lat": r.station.lat, "lon": r.station.lon},
                             station_id=r.id)
               for r in ctx.stations()
           ]
   ```

   `get_json` / `post_form` retry server errors, wait out HTTP 429 and honour
   `min_interval_s` and `timeout_s`. When the API accepts several locations
   per request (like Open-Meteo), send one grouped request for every station
   (see `bronze/_open_meteo.py`): each refresh then costs one request per source. For scrapers, store the raw HTML in `payload` (a string)
   and parse it in silver, never in bronze.
2. **Silver**: create `silver/transformer_<name>.py` with a `dataset` name, a
   polars `schema` and a `transform(batch, ctx)` that ends with `self.conform(frame)`.
3. **Config**: add the source to `config/sources.yaml` with its `attribution`.
4. **Tests**: mock HTTP with `httpx.MockTransport` (see `tests/bronze/`).
5. `uv run bluebird validate && uv run pytest`.

### Add a KPI

1. **Gold**: create `gold/aggregator_<name>.py`:

   ```python
   @register_aggregator("my_kpi")
   class AggregatorMyKpi(Aggregator):
       version: ClassVar[str] = "1"
       Params: ClassVar[type[AggregatorParams]] = MyKpiParams
       required_datasets: ClassVar[tuple[str, ...]] = ("ensemble_hourly",)

       def compute(self, ctx, ref, period) -> KpiResult | None:
           ...  # ctx.silver(...), gold/_ensemble.member_window over period.start/end,
           return self.result(ctx, ref, period, probability=..., ...)
   ```

   `compute` handles one station and one period (`period.native_window` for the
   whole-day period, `self.on_ski_day(...)` for station times); return `None`
   without enough data. Return probabilities in [0, 1]. Put explanatory values
   in `drivers`. Bump `version` whenever the computation changes.
2. **Config**: add the KPI to `config/kpis.yaml` with its `name`,
   `description`, `method` (how it is computed, with `{param}` placeholders),
   `params`, the `periods` it makes sense for and the `drivers` you want
   displayed (labels in French and English live here, not in the frontend).
3. **Tile**: add a tile in `config/tiles.yaml` (title with `{period}`) and its
   id in `config/layout.yaml`. The refresh workflow gets a gold job for it
   automatically.
4. **Tests**: synthetic silver data with a known answer (see `tests/gold/`).

No frontend change is needed for a KPI shown in a `banner`, `banner_full`,
`simple` or `ranking` tile.

### Add a Rewind (a closed season)

1. Add an entry to `config/rewinds.yaml` (`id`, `name`, `start`, `end`,
   `massifs`, `kpis`, `filter`).
2. Add its exclusive filter to `config/filters.yaml` (`exclusive: true`,
   `theme: rewind`), right after the `all` filter, and tag its historical KPIs
   with it.
3. Add one tile per KPI in `config/tiles.yaml`, of any type (`banner_full`,
   `banner`, `simple`, `ranking`, with `photo: leader` for a banner), and list
   them in `config/layout.yaml`. The tile finds its Rewind from the KPI and
   takes the theme of the Rewind's filter: no Rewind-specific option.
4. The day after `end`: `uv run bluebird rewind --rewind <id>` (or the *Build
   a Rewind* workflow), review `config/rewind/<id>/` and commit it.

### Add a historical KPI

1. Create `pipeline/src/bluebird_pipeline/gold/aggregator_season_<name>.py`:
   a `SeasonAggregator` registered with `@register_aggregator("season_<name>")`,
   whose `aggregate(ctx, rewind, hourly)` receives the `season_hourly` rows of
   the season window (helpers in `gold/_season.py`) and returns
   `self.result(rewind, ref, value=…, drivers=…)` per station.
2. Add the KPI to `config/kpis.yaml` with `kind: historical`,
   `value: {unit, decimals, scale}`, `method`, `drivers` and the Rewind filter; add it
   to the Rewind's `kpis`, then a tile (any type) and its layout entry.
3. If it needs a new variable, add it to the season source `hourly` (and to
   `silver/_open_meteo.VARIABLES` and the transformer schema), then fetch
   again; otherwise `uv run bluebird rewind --rewind <id> --no-fetch` is enough.

### Add a period

1. Add it to `config/periods.yaml` (`id`, `start`, `end`, one label per day of
   the horizon). Time slots must still cover the ski day without gap or
   overlap: shorten a neighbour.
2. List it in the `periods` of the KPIs that should compute it.
3. `uv run bluebird validate && uv run pytest`, then `uv run bluebird demo`.

The site creates its tiles from the payload; no frontend change is needed.

### Add a tile type

1. Create `web/src/tiles/TileXyz.svelte` (naming convention: type `xyz` →
   `TileXyz`, checked by a test). It receives `TileProps` (`tile` with a
   unique `id` and the title of its period, `kpis`, and `data`: the payload
   narrowed to one period, where `data.kpis[id]` has `ranking`, `generated_at`
   and `stale`). Wrap it in the shared card frame (`<section class="card"><div
   class="card-body">…`) or in `TileShell` for a list-style tile, and reuse
   `StationRow` / `StationDetails` to show stations. Read options with
   `numberOption` / `booleanOption` / `stringOption` from `tiles/options.ts`.
2. Register it in `web/src/tiles/registry.ts` under the id `xyz`, and map it
   to a loading placeholder shape in `skeletonVariant` (same file).
3. Use `type: xyz` in `config/tiles.yaml`.
4. If it needs new data, add a `Displayer` in `pipeline/.../diamond/` or extend
   the diamond models, then run `uv run bluebird schemas` and `npm run gen:types`.

### Add a filter (filter bar)

1. Add an entry to `config/filters.yaml` (`id`, `name {fr, en}`, `icon`).
2. Tag the KPIs it should show with its id: `filters: [<id>]` in `config/kpis.yaml`.
3. `uv run bluebird validate` (a filter matching no enabled KPI is an error).

The first filter is selected by default; `all: true` makes a filter show
every tile. Filters matching no tile of the current layout are hidden.

### Add a banner photo

1. Put the photo in `web/src/assets/photos/<massif>/<station_id>/<station_id>_<n>.webp`
   (one folder per massif, then per station; files named with the station id
   and a number, e.g. `cauterets_1.jpg`, `cauterets_2.jpg`), or any other path
   for a fixed tile photo. Landscape, at least
   1200 × 600 px, ideally < 300 KB.
2. Add its author and licence to `web/src/assets/photos/credits.yaml`
   (publication rights are required; the credit is shown at the bottom of
   the tile back and on the legal notice page, never on the banner).
3. Set `photo: leader` (or `photo: <path>` without extension) in the tile
   options of `config/tiles.yaml`. Without a matching photo, the tile shows
   its illustration, so `leader` is safe even when only some stations have one.

### Add a page (footer link)

1. Add an entry under `pages:` in `config/pages.yaml`: `id` (also the URL
   hash, `#<id>`), `title {fr, en}` and `sections`, each with `paragraphs`,
   `links` and/or a built-in `block` (`data_sources`, `photo_credits`,
   `service_*`).
2. List its id in `footer.pages` to link it from the footer.
3. `uv run bluebird validate` (unknown footer pages, duplicate ids and empty
   sections are errors).

No frontend change is needed: `InfoPage.svelte` renders every page in a
full-window `Sheet`. To show something else in a sheet (a station page…),
render your own content in `components/Sheet.svelte` and drive it with
`sheets.open(id)` / `sheets.close()` from `lib/sheets.svelte.ts`. A new
built-in block is a new value of `PageSection.block` in `config.py` plus its
rendering in `InfoPage.svelte`.

### Reorder tiles

Edit `config/layout.yaml`. `default` applies to every massif; `overrides`
replaces it for one massif. Merging the change into `main` redeploys the site.

### Add a UI language

1. Add the locale to `LOCALES` in `web/src/lib/i18n/core.ts` and create
   `web/src/lib/i18n/<locale>.json` with the same keys as `fr.json`.
2. Add the field to `Localized` in `pipeline/src/bluebird_pipeline/config.py`
   and translate every `{fr, en}` label in `config/`.
3. `uv run bluebird schemas`, `npm run gen:types`, and the tests.

### Add a reference source (slow-changing data)

For data that changes once a season or less (terrain, piste maps, resort
facts), use `schedule: reference` in `config/sources.yaml`. The Extractor is
written as usual. The Transformer additionally sets `reference_suffix` (e.g.
`".geojson"`) and implements `reference_file(frame, massif, ctx)` (deterministic
serialisation of one massif) and `read_reference(content)` (the inverse). See
`silver/transformer_osm_overpass.py`. Then run `uv run bluebird reference`,
review and commit `config/reference/`. Consumers read it with
`ctx.reference("<dataset>")`.

### Add a storage backend

Implement `write_bytes`, `read_bytes`, `exists` and `list` of
`storage/base.py::Storage` (e.g. S3), and select it in `cli.py`.

## Frontend

- **Stack**: Svelte 5 (runes), TypeScript, Vite. No UI framework, about
  32 KB of gzipped JavaScript.
- **Fonts**: Plus Jakarta Sans (text) and Barlow Semi Condensed ExtraBold
  Italic (logo, titles, percentages), both OFL-licensed and self-hosted
  through `@fontsource` packages: no font CDN, the browser only downloads the
  subsets it needs. Tokens `--font-sans` and `--font-display`.
- **Data flow**: `src/lib/config.ts` imports `config/*.yaml` at build time
  through `@rollup/plugin-yaml`. `src/lib/data.ts` fetches
  `./data/diamond/<massif>/latest.json` and `./data/diamond/status.json` at
  runtime (relative URLs, so the site works under any GitHub Pages path). A
  404 shows an "upcoming data" state; a missing status only affects the
  service status page.
- **Tiles per period**: `src/lib/periods.ts` expands every configured tile
  into one tile per period of the payload (`expandTiles`), ordered by start
  time then layout order, titled from the template (`Neige {period}`). Labels
  ("ce soir", "demain matin") are relative to the ski day of the payload, or
  of the visitor's clock when a refresh is late. The page keeps a reactive
  clock (`now` in `App.svelte`) that ticks when the next period ends, every
  minute and when the tab is shown again, so a tile leaves as soon as its
  period is over. Values kept from an earlier refresh show a "data from
  HH:MM" badge (`StaleBadge.svelte`); a period without values says the data
  is unavailable.
- **Service status**: a full-window page like the privacy page (`#status`,
  page `status` of `config/pages.yaml`, linked from the footer with a small
  state dot). Its sections use the `service_*` blocks, rendered by
  `components/ServiceStatus.svelte` from `status.json` (`lib/status.ts`):
  overall state with the number of degraded items and the refresh time, then
  one line per data source, transformation, KPI and tile of the current
  massif, each with an icon and a word (`--state-*` tokens). Periods already
  over are not listed. `App.svelte` passes the status, massif, timezone and
  clock to every `InfoPage` (`service` prop).
- **i18n**: UI strings in `src/lib/i18n/{fr,en}.json`; content labels come
  from the YAML `{fr, en}` objects. The language follows the browser, can be
  switched in the menu and is remembered in `localStorage`.
- **Header and menu**: the "Bluebird" wordmark on the left (text only,
  `components/Logo.svelte`; the favicon keeps the mountain mark), a menu
  button on the right. The menu (`components/AppMenu.svelte`) slides in over a blurred
  backdrop, locks page scrolling (`lib/scrollLock.ts`), makes the page inert,
  closes with Escape, and holds the language choice.
- **Massif bar**: under the wordmark, one chip per enabled massif of
  `config/massifs.yaml` (no "all" choice: one massif is always shown). It is
  the only place to choose the massif. `components/FilterBar.svelte` with
  `size="large"`; the choice is remembered in `localStorage`.
- **Filter bar**: under the massif bar, the same component with smaller chips
  (`size="small"`), from `config/filters.yaml`. A filter shows the tiles whose KPIs carry its id;
  the choice is remembered in `localStorage`. "All" shows every tile except
  those of `exclusive` filters (the Rewinds), which only show under their own
  chip; `theme: rewind` makes a chip Christmas red.
- **Design**: betting-app layout (inspired by Betclic) in dark blue, light
  blue and white, on a plain, sober page background with no background
  animation. Colours are role tokens in `styles/tokens.css` (light and dark
  mode); only the sticky header uses a frosted "Liquid Glass" surface
  (`styles/glass.css`). Cards share a frame with light-blue diagonal stripes
  at the top corners (`.card` in `styles/base.css`).
- **Tile types** (`config/tiles.yaml`, component `Tile` + PascalCase of the type):
  - `banner` (`TileBanner.svelte`): a banner (photo, or a static SVG
    illustration from `components/BannerArt.svelte` with scenes `snowfall`,
    `piste`, `offpiste`, `mountain` and ridges from the massif `skyline`)
    with the "?" button, the KPI title, the best stations as light-blue "odds
    buttons" (short name, percentage and three reliability dots from the
    station `confidence`, `components/ConfidenceDots.svelte`) with a
    probability bar below each (`OddsRow.svelte`), and "see all" for the rest
    (`RankingMore.svelte`). Each row of the rest shows its reliability dots
    right of the name (`StationRow.svelte`). While the list is open, a second
    "see less" button sits between the top stations and the list, so it can
    be closed without scrolling down.
  - Station details (`StationDetails.svelte`: drivers, reliability,
    elevation) open on tap only when the tile option `details: true` is set.
    It is off by default for now: odds boxes and rows are then static
    (`data-no-flip`, full summary in a visually hidden text) and a tap on
    them does nothing.
  - `banner_full` (`TileBannerFull.svelte`): same content, with the photo or
    illustration filling the whole card behind the title and odds, like the
    "live match" cards of betting apps. Used by the snowfall tile today.
  - `simple` (`TileSimple.svelte`): the same parts without any banner (title
    without icon, odds buttons, "see all"), so the card is shorter. Meant
    for the KPIs lower on the page; used by the off-piste powder tile today.
    Options `top`, `show_odds` and `details`.
  - `ranking` (`TileRanking.svelte`): a compact list of every station.
- **Live and historical KPIs in the same tiles**: every tile type receives a
  `KpiView` (`lib/kpiView.ts`), built by `viewFor()` in `App.svelte`:
  - `live`: probabilities from the daily payload, with confidence and
    details; `null` while it loads (the tile shows its placeholder);
  - `historical`: Rewind values from `config/rewind/<id>/<massif>.json`,
    bundled at build time (`rewindPayload()` in `lib/config.ts`), so these
    tiles show even while live data loads or fails. The Rewind is found from
    the KPI (`rewinds.yaml`). Values are formatted with the KPI `value` unit
    ("4,43 m", "46 h", "51 %"), bars go up to `value.max` when set (0–100 %
    for a percentage) or else are relative to the best value,
    and there are no reliability dots, odds or details.
  `tiles/tileModel.ts` turns a tile and its view into what the components
  show (top/rest, photo, scene, odds, details, empty message, badge, theme);
  `OddsRow`, `StationRow`, `RankingMore`, `ValuePill` and `KpiBack` render
  `RankItem`s of either kind. A new kind of data only needs a view builder.
- **Tile themes**: a tile's colours come from token overrides on its card
  (`[data-tile-theme]` in `styles/base.css`, set by `FlipCard theme`). A
  historical tile takes the `theme` of its Rewind's filter (`rewind`:
  Christmas red, red stripes, red podium and pills) and a "REWIND 25/26"
  badge (`TileBadge.svelte`); the tile option `theme` overrides it. A new
  theme is one CSS block and one value in `TILE_THEMES`.
- With a Rewind filter active, the line above the tiles shows the season
  period instead of the update time.
- **Data date**: above the tiles, as plain text on the page (no card),
  `components/ForecastStatus.svelte` shows the reference date of the data
  (the day of `generated_at` in the massif timezone) and a small line with
  the update time. The massif is not repeated there.
- **Footer**: two short centred lines (`components/AppFooter.svelte`, from
  `config/pages.yaml`): the GitHub logo linking to the repository, then small
  links to the pages (about, service status with its state dot, legal notice,
  privacy). Long texts (method, avalanche disclaimer, sources) live in those
  pages, not in the footer. A dot separates the links and ends its line, so
  a wrapped line never starts with one.
- **Full-window pages (sheets)**: `components/Sheet.svelte` is a generic
  over-page covering the whole window with a strong Liquid Glass surface
  (`--sheet-bg`, `--sheet-blur`; opaque with reduced transparency), a title,
  a close button in the top-right corner and scrollable content. It rises
  from the bottom when it opens and slides back down when it closes (`rise`
  in `lib/transitions.ts`). Scroll is locked, the page behind is inert, Escape
  closes it and focus returns to the link that opened it.
  `lib/sheets.svelte.ts` keeps the open sheet in the URL hash (`#legal`), so
  pages can be linked to and the phone "back" gesture closes them.
  `components/InfoPage.svelte` renders each page of `config/pages.yaml` in a
  sheet, with the built-in blocks `data_sources` (attributions of
  `config/sources.yaml`), `photo_credits` (`credits.yaml`, labelled with the
  station name) and `service_*` (service status, see above).
- **Photos**: `lib/photos.ts` bundles `src/assets/photos/**` at build time.
  Tile option `photo`: `none` (default), `leader` (a random photo of the ski
  area ranked first, among `<massif>/<station_id>/<station_id>_<n>.*`, drawn
  once per station and page load), or a fixed path. Missing photos fall
  back to the illustration. Credits come from `credits.yaml`; they are not
  shown on the banner but in the last section of the tile back ("Photo
  credit", after the sources) and on the legal notice page.
- **Tile back**: every tile is a `FlipCard`. The "?" button in its top-right
  corner (or a tap anywhere outside the odds buttons, station rows, "see all"
  and station details) turns it over to `KpiBack`, one section per topic: what the KPI
  measures (its description, which is not repeated on the front), the time
  window studied, how it is computed (`method` from `kpis.yaml` with its params
  filled in), the reliability for its period (index, level, station breakdown, scenarios),
  the last update, the data sources and the photo credit. The
  "×" button, or a tap on the back, turns it back. The hidden side is inert.
  Each face has its own card frame, so the striped top corners turn with the
  card and stay on its edges during and after the flip.
- **Equal sizes**: every banner tile has the same collapsed size, set by
  `--tile-banner-h`, `--tile-front-h` and `--tile-more-h` in `styles/base.css`;
  every `simple` tile has the shorter `--tile-simple-h`, and every odds button
  the height `--odds-button-h`;
  titles, descriptions, names and odds buttons are clamped to fixed heights
  (long titles such as "… demain après-midi" use a smaller font on up to two
  lines).
  Stations show their `short_name`; full names stay in accessible labels.
- **Filter transitions**: changing filter makes tiles arrive "from the back"
  (scale, fade and rise, staggered), leaving tiles fade out and the others
  glide into place (`lib/transitions.ts`, `animate:flip`). Durations drop to 0
  with "reduce motion". The filter row scrolls horizontally (swipe, trackpad,
  or mouse wheel on desktop) with fading edges when chips are hidden.
- **Accessibility**: text keeps ≥ 4.5:1 contrast (odds buttons use one fixed
  colour pair; magnitude is shown by the bars). Reduced transparency and
  missing `backdrop-filter` fall back to an opaque header. Buttons expose
  their state with `aria-pressed` / `aria-expanded`.
- **Mobile first**: one column, two from 768 px, three from 1100 px.

### Tiles on the site

Configured in `config/tiles.yaml`, in the order of `config/layout.yaml`.
Keep this table in sync when a tile is added, removed or changed.

| Tile id | Type | KPI (kind) | Filter | Title (fr / en) | Options |
|---|---|---|---|---|---|
| `snowfall_today` | `banner_full` | `snowfall_chance` (live: day, morning, midday, afternoon, evening, night) | Snow | Neige {period} / Snow {period} | `photo: leader`, `scene: snowfall` |
| `onpiste_powder` | `banner` | `onpiste_powder_chance` (live: morning, midday, afternoon) | Powder | Poudreuse sur piste {period} / On-piste powder {period} | `photo: leader`, `scene: piste` |
| `offpiste_powder` | `simple` | `offpiste_powder_chance` (live: morning, midday, afternoon) | Powder | Poudreuse hors-piste {period} / Off-piste powder {period} | — |
| `whiteout` | `simple` | `whiteout_chance` (live: day) | Visibility | Jour blanc {period} / White day {period} ("aujourd'hui", "demain") | `top: 3` |
| `rewind_2025_26_total_snowfall` | `banner_full` | `season_total_snowfall` (historical, m) | Rewind 25/26 | Le plus de neige / Most snow | `photo: leader`, `scene: snowfall` |
| `rewind_2025_26_longest_snowfall` | `banner` | `season_longest_snowfall` (historical, h) | Rewind 25/26 | La plus longue chute de neige / Longest snowfall | `photo: leader`, `scene: snowfall` |
| `rewind_2025_26_domain_snowfall` | `banner` | `season_domain_snowfall` (historical, m) | Rewind 25/26 | Le plus de neige sur le domaine / Most snow on the slopes | `photo: leader`, `scene: piste` |
| `rewind_2025_26_offpiste_snowfall` | `banner` | `season_offpiste_snowfall` (historical, m) | Rewind 25/26 | Le plus de neige hors-piste / Most off-piste snow | `photo: leader`, `scene: offpiste` |
| `rewind_2025_26_deep_snow_days` | `banner` | `season_deep_snow_days` (historical, %, bars 0–100 %) | Rewind 25/26 | L'enneigement idéal / Ideal snow cover | `photo: leader`, `scene: piste` |
| `rewind_2025_26_white_days` | `banner` | `season_white_days` (historical, days, fewest first) | Rewind 25/26 | Le moins de jours blancs / Fewest white days | `photo: leader`, `scene: mountain` |

Live tiles show under "All" and their filter, once per period of today and
tomorrow not over yet (`{period}` becomes "ce soir", "demain matin"…); Rewind
tiles only under their exclusive Rewind filter, once, in the Rewind theme with
a "REWIND 25/26" badge.

### Future features (roadmap)

Ideas under study; future KPIs are listed in PROJECT.md ("Future
indicators"). Feasibility: 🟢 data already in the project or one more
Open-Meteo variable (no key); 🟡 new open, free source (open data, API without
key); 🔴 API key, scraping or agreement needed (needs the owner's approval,
AGENTS.md §4; scraping must respect the site's terms).

| Feature | What it does | Data and approach | Feasibility |
|---|---|---|---|
| Webcams | Resort webcams on the tile back or as banner; also a way to calibrate white days (image brightness and contrast) | Public webcam links/images of the resorts | 🔴 |
| Resort opening status | Share of pistes and lifts open, per station | Resort websites / N'PY (scraper, terms to check) | 🔴 |
| Near me | Sort resorts by conditions × travel time | Browser geolocation (never stored) + public routing (OSRM) | 🟡 |
| Value for money | Lift pass price per km of pistes | Prices (scraper) + piste km from `domain_features` | 🔴 |
| Ski area map | Map tile of pistes and lifts | `domain_features` (already collected) | 🟢 |
| Comparator | Two resorts side by side on every KPI | Existing payloads | 🟢 |
| Slope aspect and steepness | Refine powder KPIs (north faces keep powder) | IGN RGE ALTI or Copernicus DEM | 🟡 |
| Rewind calendar | Season timeline: storms, white days, bluebird days | Committed season hourly file | 🟢 |
| All Time data | Season ranks since 1950, trends, records, "when to go" | Open-Meteo ERA5-Land (1950, 9 km) or CERRA (1985–2021, 5.5 km), as a new `schedule: season`-like archive; Météo-France snow observations (open data) to validate | 🟢/🟡 |
| Avalanche bulletin (BRA) | Danger level per massif, archive for Rewind/All Time | Météo-France API (key) or public XML/PDF archive | 🔴 |
| School holidays | Crowd index, "holiday luck" Rewind | Open data school calendar (education.gouv) | 🟡 |
| Probability calibration | "Our success rate" (Brier score, reliability diagram) | Gold history on `gh-pages` vs observed snow | 🟢/🟡 |

**Tile ordering algorithm (planned).** The page order would become a score
per tile, computed in the browser and explained on the tile back ("why this
tile is here"):

`score = wP · popularity + wR · relevance + wF · reliability`

- **Popularity** (0–1, defined by the owner) without tracking, to keep the
  privacy promise: an editorial weight in `tiles.yaml`, and/or local
  preferences of the device (tiles opened or flipped, in `localStorage`,
  never sent).
- **Relevance** (0–1) from the data: intensity (highest probability or value
  of the ranking), context (season phase, time of day: "tomorrow" tiles rise
  in the afternoon), novelty (change since yesterday, gold history), alerts
  (wind, cold or rain above a threshold go first).
- **Reliability** (0–1): the day's reliability index (already on the tile
  back), data freshness (stale data penalised), station coverage.
- **Rules**: pinned tiles first; tiles without data hidden; hysteresis (a tile
  moves up only when its score beats its neighbour by a margin) so the page
  does not reshuffle at every visit; no filter takes all the top slots.

Planned implementation: a pure, tested `rankTiles(tiles, views, signals,
weights)` in `web/src/lib/`, and `ordering: { mode: fixed | scored, weights,
pinned }` in `config/layout.yaml`, `fixed` (today's behaviour) by default.

**Constraints.** No push notifications (no server: hosting stays on GitHub);
no audience tracking (see the Privacy page); every new source declares its
attribution in `config/sources.yaml` and stays within its rate limits.

## Testing and quality

| Area | Tooling | Run |
|---|---|---|
| Python format and lint | ruff | `uv run ruff format --check . && uv run ruff check .` |
| Python tests | pytest (no network: HTTP is mocked) | `uv run pytest` |
| Config | pydantic + cross-checks | `uv run bluebird validate` |
| Schema drift | generated vs committed | `uv run bluebird schemas --check`, `npm run gen:types && git diff --exit-code` |
| Types | svelte-check (TypeScript 6) | `npm run check` |
| Frontend tests | Vitest | `npm test` |
| Workflows | actionlint | runs in CI |

Notable tests: KPI models on synthetic data with known answers (per
period), Open-Meteo key parsing on the real naming scheme, one grouped
request per source, rate-limit handling, ski-day and period boundaries
(including summer time), the gold fallback (stale values), the status
builder, a full bronze → diamond run, a simulated CI chain (`plan`, one gold
job per KPI, `status` with a missing report), the plugin naming convention,
i18n key parity, tile expansion and hiding of ended periods, and a check
that every tile type in the config has a component.

## Git workflow and deployment

`main` is the only long-lived branch and the default branch. Work happens on
short-lived branches created from `main` and merged back through a pull request.

| Branch | Who writes | How | Protection (rulesets) |
|---|---|---|---|
| `main` | nobody directly | pull request, "CI result" must pass | no push, no force push, no deletion |
| `feat/…`, `fix/…`, `docs/…` | developers and agents | normal push / pull, one branch per change, deleted after merge | none |
| `reference/refresh-…` | the *Refresh reference data* workflow | one branch per refresh, then a pull request | none |
| `rewind/<id>-…` | the *Build a Rewind* workflow | one branch per build, then a pull request | none |
| `gh-pages` | GitHub Actions only | built site + refreshed data | no push, no PR merge, no deletion; only the deploy key bypasses |

| Workflow | Trigger | Job |
|---|---|---|
| `ci.yml` | PR to `main`, push to `main` (after merge), manual | Python + web checks, actionlint; `CI result` is the required check |
| `deploy.yml` | push to `main` (= merged PR), manual | build `web/`, publish to `gh-pages`, keep `data/` |
| `refresh.yml` | 00:07, 06:07, 12:07 and 18:07 Paris, Nov–May, manual | one pipeline per layer from `main` (see below), publish gold + diamond + status to `gh-pages/data/` |
| `reference.yml` | manual, once a season | refresh `config/reference/` from reference sources, open a PR to `main` |
| `rewind.yml` | manual, the day after a season ends | build `config/rewind/<id>/` (input `rewind`, optional `no_fetch`), open a PR to `main` |
| `guard-gh-pages.yml` | PR opened against `gh-pages` | close it with an explanation |

`deploy.yml` and `refresh.yml` share a concurrency group, so they never push
to `gh-pages` at the same time. Both push with the `GH_PAGES_DEPLOY_KEY`
deploy key; both fail early with a clear message if it is missing.

### The refresh workflow

```
plan ─▶ bronze[source] ─▶ silver[source] ─▶ gold[KPI] ─▶ diamond[massif] ─▶ status ─▶ publish
```

| Job | One per | What it does |
|---|---|---|
| `plan` | — | Gate, then `bluebird plan --json`: run id, sources, datasets, KPIs, massifs (the matrices). |
| `bronze` | source | `run --layer bronze --source S`: one grouped API request. |
| `silver` | source | Downloads its bronze artifact, `run --layer silver --source S`. |
| `gold` | KPI | Restores published data, downloads every silver dataset, `run --layer gold --kpi K`. |
| `diamond` | massif | Restores published data, downloads the gold files, `run --layer diamond --massif M`. |
| `status` | — | Always runs: `bluebird status` writes `status.json`, the manifest and the job summary. |
| `publish` | — | The only job with the deploy key: publishes gold, diamond and status in one commit. |

- **Schedule.** GitHub cron is in UTC, so there is one cron line per Paris
  offset (`7 23,5,11,17 * 1-3,10-12 *` for UTC+1, `7 22,4,10,16 * 3-5 *` for
  UTC+2). The `plan` job compares `github.event.schedule` with the current
  offset of Europe/Paris and the local month: the other line and
  out-of-season runs stop there, without any API call.
- **Isolation.** Matrices use `fail-fast: false` and later jobs run with
  `if: always()`, so a failing source only affects the KPIs that need it,
  which fall back to their last valid values. Every job passes `--run-id` from
  `plan`, so they agree on the ski day and the visible periods.
- **Artifacts.** Files move between jobs as artifacts (`--export`): bronze
  and silver are kept 7 days for debugging, reports 7 days.
- **Setup.** `.github/actions/setup-pipeline` installs uv and the pipeline
  (without dev tools, `UV_NO_SYNC=1`) and sets `BLUEBIRD_DATA_DIR`.
- **Cost.** About ten short jobs per refresh (4–5 minutes wall time); free on
  a public repository.

### First-time GitHub setup

```bash
git remote add origin git@github.com:<you>/bluebird.git
git push -u origin main               # the first deploy run fails: no key yet, that's expected
scripts/setup-github.sh               # needs `gh auth login` with admin rights
```

The script is idempotent. It makes `main` the default branch (and deletes a
leftover `dev` branch if it is fully merged), creates the deploy key and
secret, creates or updates the two rulesets, allows workflows to open pull
requests, triggers the first site build, configures Pages to
serve `gh-pages`, and runs the data refresh workflow once. Options: `--rotate-key`,
`--no-runs`. Rulesets and Pages are free on public repositories; private
repositories need GitHub Pro or higher.

### Day-to-day

```bash
git switch main && git pull
git switch -c feat/my-change
# …work, commit…
git push -u origin feat/my-change
gh pr create --base main              # CI runs; merge when green
git switch main && git pull && git branch -d feat/my-change
```

Merging into `main` deploys the site.

Scheduled workflows only run on the default branch and can start several
minutes late. GitHub disables schedules in public repositories after 60 days
without activity: re-enable `Data refresh` in the Actions tab at the start of
a season if needed.

After a change of the diamond `schema_version` (2 since periods), the site
deployed on merge cannot read the data published before: run the `Data
refresh` workflow manually right after the merge (outside the season too).

## Data sources, limits and licences

| Source | Used for | Licence / terms |
|---|---|---|
| Open-Meteo Ensemble API (ECMWF IFS ENS 51 members, DWD ICON-EPS 40 members) | All KPI probabilities | CC BY 4.0; free API for non-commercial use |
| Open-Meteo Forecast API (Météo-France AROME/ARPEGE) | Deterministic drivers | CC BY 4.0; free API for non-commercial use |
| OpenStreetMap Overpass (reference, once a season) | Pistes and lifts per station, with geometry; Rewind domain and off-piste points | ODbL |
| Open-Meteo Historical Forecast API (Météo-France AROME HD 1.5 km, archived since late 2022) | Rewind historical KPIs (season snowfall, longest snowfall; sunshine, cloud cover and weather code kept for future KPIs) | CC BY 4.0; free API for non-commercial use |
| Open-Meteo Historical Forecast API (Météo-France AROME: humidity, low cloud, radiation) | Rewind white days (`open_meteo_historical_light`, station and domain points) | CC BY 4.0; free API for non-commercial use |
| Open-Meteo Historical Forecast API (DWD ICON, `icon_seamless`, ~7 km over the Pyrenees) | Rewind snow depth on the ground (AROME has none in the archive): ideal snow cover days | CC BY 4.0; free API for non-commercial use |

- Open-Meteo weighs ensemble requests by member count, and counts every
  location of a grouped request. The free tier allows roughly 600 weighted
  calls per minute and 10,000 per day. Bluebird sends one grouped request per
  source and refresh (2 HTTP requests, 4 times a day); a full Pyrenees
  ensemble response (36 locations, 3 days, 91 members) is about 1 MB gzipped.
  The daily quota is what to watch when adding massifs or forecast days.
  Extractors wait out HTTP 429 and can split requests
  (`max_locations_per_request`). Request only the bands and days the KPIs need.
- Open-Meteo counts a request covering more than two weeks per location as
  several calls (a five-month season ≈ 11 calls per point). A Pyrenees Rewind
  (18 stations × up to 17 points) weighs about 3,400 calls: the season source
  spaces its requests (`min_interval_s: 20`), so a build takes 10–15 minutes.
- Rewind values come from archived *forecasts* of a model (AROME HD, 1.5 km),
  not from snow measurements: compare resorts with them, do not read them as
  official snow reports.
- Commercial use requires an Open-Meteo API subscription.
- Attribution from `sources.yaml` is displayed on each tile back (sources of
  the day) and on the "About" page (every enabled source).
- The public Overpass server is slow and often returns 429/504; the
  extractor retries. It is a reference source: refreshed once a season, never daily.
- Pistes and lifts are selected within `radius_m` (4 km) of each station, so
  neighbouring resorts share some features (Peyragudes/Val Louron,
  Font-Romeu/Les Angles) and large domains are under-counted (Saint-Lary,
  Grand Tourmalet). Selecting by the OSM `landuse=winter_sports` area is the
  planned improvement; until then, do not display these totals as official figures.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `ModuleNotFoundError: bluebird_pipeline` | Virtualenv inside iCloud (hidden `.pth`). Set `UV_PROJECT_ENVIRONMENT` outside iCloud and `uv sync` again. |
| `Configuration error: … Extra inputs are not permitted` | Typo or unknown key in YAML. A comma inside an unquoted flow-mapping value (`{ fr: a, b }`) also splits it: quote the value. |
| `rate limited (HTTP 429), waiting 65s` | Normal with Open-Meteo bursts; the run continues. Many in a row: lower the request weight (bands, days, models). |
| `Stale schemas` in CI | Run `uv run bluebird schemas` and `npm run gen:types`, commit both. |
| `svelte-check` complains about TypeScript 7 | The project pins TypeScript 6 until svelte-check supports TypeScript 7 alone. |
| Site shows "No forecast yet" | No `latest.json` on `gh-pages` yet: run the `Data refresh` workflow. |
| Site cannot load the forecasts after a merge | The published data has an older `schema_version`: run the `Data refresh` workflow manually. |
| Footer shows degraded items, or tiles show "data from 06:00" | A source, KPI or job failed during the last refresh. Open the run in the Actions tab: its summary lists every unit with the error message; bronze/silver artifacts help debugging. |
| Site shows an old date | The refreshes failed or are out of season. Check the Actions tab. |
| Deploy fails with "GH_PAGES_DEPLOY_KEY is missing" | Run `scripts/setup-github.sh`. |
| `warning: config/reference/… is missing` | A new massif or reference source has no reference file yet: run `uv run bluebird reference --massif <id>` (or the *Refresh reference data* workflow). |
| *Refresh reference data* cannot open its pull request | Run `scripts/setup-github.sh` again: it allows workflows to create pull requests. |

## Documentation rule

Every change to the project updates the documentation in the same pull
request: README.md for developers, CONTEXT.md for AI agents, PROJECT.md for
site users. AI agents follow this and the other rules in [AGENTS.md](AGENTS.md).

## License

Not chosen yet. Add a `LICENSE` file before accepting outside contributions.
