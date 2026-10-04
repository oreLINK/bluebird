# CONTEXT.md — briefing for AI coding assistants

Read this file before changing anything in the repository. It states what
Bluebird is, how the code is organised, the invariants you must keep, and the
exact commands that prove a change works. Human-oriented docs:
[README.md](README.md) (developers) and [PROJECT.md](PROJECT.md) (product).

The mandatory rules for every prompt (documentation updates, languages, Git,
quality bar, end-of-task checklist) are in [AGENTS.md](AGENTS.md). Claude Code
loads both files through `CLAUDE.md`; Codex reads `AGENTS.md` natively.

## 1. What the project is

- A **static website** (Svelte 5 + Vite, mobile first) showing, refreshed
  every 6 hours (00:00, 06:00, 12:00, 18:00 Paris, Nov–May), the probability
  of good ski conditions in French ski resorts, per **period** of today and
  tomorrow (morning, lunchtime, afternoon, evening, night, whole day).
- A **Python data pipeline** that fetches weather forecasts, computes the
  probabilities, and writes small JSON files the website reads.
- First massif: Pyrenees, 18 stations. Four **live** KPIs (probabilities per
  period): `snowfall_chance`, `onpiste_powder_chance`, `offpiste_powder_chance`
  and, under the **Visibility** filter, `whiteout_chance` (period `day` only:
  white day today and tomorrow).
- **Rewinds** review a closed season with **historical** KPIs (values, not
  probabilities), built once by `bluebird rewind`. First instance: *Rewind
  25/26* (2025-12-01 → 2026-05-01, Pyrenees): `season_total_snowfall`,
  `season_longest_snowfall`, `season_domain_snowfall`, `season_offpiste_snowfall`,
  `season_deep_snow_days` (% of days with > 70 cm on average over the slopes,
  ICON snow depth), `season_white_days` (fewest first, `order: asc`). The info
  line above the tiles reads "Saison 2025/2026". Shown only under its exclusive
  Christmas-red filter, right after "All". Rewind tiles are not split by period.
- The UI mimics a sports-betting page: one tile per live KPI and period (tile
  templates in `tiles.yaml` are expanded per period, "Neige {period}"),
  stations ranked by descending probability. A tile disappears when its
  period ends. The footer shows the service status of the last refresh. Style: betting-app look (Betclic-like) in dark
  blue, light blue and white, sober plain background, no background animation.
  Header: "Bluebird" wordmark (text only) left, menu (language) right;
  below, the massif bar (large chips, no "all", the only massif choice) then
  the filter bar (small chips). Above the tiles, plain text (no card): data date (day of
  `generated_at`) and update time. Station details on tap are off for now
  (tile option `details`, default false): the tiles show the probability only.
- UI languages: French (default) and English. **All code, comments, docs and
  commit messages are in English.** User-facing strings are in both languages.
- Hosting and storage: **GitHub only** (Pages + the `gh-pages` branch). No
  server, no database, no cloud bucket.

## 2. Repository map

| Path | Role |
|---|---|
| `AGENTS.md` | Mandatory rules for AI agents, applied on every prompt. |
| `CLAUDE.md` | Imports `AGENTS.md` and `CONTEXT.md` for Claude Code. |
| `config/filters.yaml` | Filter bar chips; KPIs opt in with `filters: [id]` in `kpis.yaml`. |
| `config/periods.yaml` | `day_start` (06:00), `horizon_days`, periods (time slots covering the ski day + `day` with `native_window`) and their labels per day. |
| `config/rewinds.yaml` | Rewinds: season `start`/`end` (local days, included), massifs, historical KPIs, exclusive filter. |
| `config/rewind/<id>/<massif>.hourly.parquet`, `.json` | **Generated** by `bluebird rewind`, committed via PR: the season hour by hour (silver `season_hourly`) and the ranked payload the site bundles. Never edit by hand. |
| `config/pages.yaml` | Footer (GitHub repository link, page links) and full-window pages (about, legal notice, privacy) with `{fr, en}` sections and built-in blocks. |
| `config/*.yaml`, `config/stations/*.yaml` | Single source of truth for massifs, stations, KPIs, tiles, layout, sources. Human-edited. |
| `config/reference/<dataset>/<massif>.geojson` | **Fetched** reference data (pistes, lifts) written by `bluebird reference`, committed via PR. Never edit by hand. |
| `config/schemas/*.schema.json` | **Generated** by `uv run bluebird schemas`. Never edit by hand. |
| `pipeline/src/bluebird_pipeline/config.py` | Strict pydantic models for every YAML file + cross-file checks. |
| `pipeline/src/bluebird_pipeline/registry.py` | `Registry` class + `load_plugins()` autodiscovery of the 4 layer packages. |
| `pipeline/src/bluebird_pipeline/context.py` | `RunContext`: config, storage, `run_date` (= ski day), `run_id` (can be pinned), `period_instances()`, silver access, local-time helpers; `PeriodInstance`. |
| `pipeline/src/bluebird_pipeline/runner.py` | Runs layers in order; isolates failures per source / KPI / massif; `RunReport` with step reports; `run_gold_kpi` (gold fallback); `finalize`. |
| `pipeline/src/bluebird_pipeline/report.py` | `StepReport`, `ReportFile`, states `ok/partial/stale/down`, `worst()`. |
| `pipeline/src/bluebird_pipeline/bronze/` | `base.py` (`Extractor`, `BronzeRecord`, `BronzeBatch`, HTTP retry/throttle) + `extractor_*.py`. |
| `pipeline/src/bluebird_pipeline/silver/` | `base.py` (`Transformer`, `conform`) + `transformer_*.py` + `_open_meteo.py` parser. |
| `pipeline/src/bluebird_pipeline/gold/` | `base.py` (`Aggregator` with `compute(ctx, ref, period)`, `KpiResult`, gold I/O, `read_gold`) + `aggregator_*.py` + `_ensemble.py` helpers. |
| `pipeline/src/bluebird_pipeline/diamond/` | `base.py` (`Displayer`), `models.py` (**frontend contract**: massif payload v2, manifest, status), `displayer_*.py`, `_status.py` (status.json, manifest, job summary). |
| `pipeline/src/bluebird_pipeline/storage/` | `Storage` ABC, `LocalStorage`, key conventions in `keys.py`. |
| `pipeline/src/bluebird_pipeline/reference.py` | Reference data: `refresh_references()`, `load_reference()`, `missing_references()`. |
| `pipeline/src/bluebird_pipeline/rewind.py` | Rewinds: `run_rewind()` (bronze → committed hourly file → gold → committed payload), `load_season()`, `is_over()`. |
| `pipeline/src/bluebird_pipeline/geo.py` | `distance_m`, `path_length_m`, `offset` on `[lon, lat]` points (shared by layers). |
| `pipeline/src/bluebird_pipeline/bronze/_season_points.py`, `extractor_open_meteo_historical.py` | Deterministic Rewind sampling points (station, domain along pistes, off-piste ring) and the season archive extractor (2 requests per station). |
| `pipeline/src/bluebird_pipeline/gold/_whiteout.py`, `aggregator_whiteout_chance.py`, `aggregator_season_white_days.py` | White days: `WhiteoutRule` (params shared by both KPIs), clear-sky radiation (`clear_sky_expr`), white hour rule; live probability (period `day`: today and tomorrow) and season count. |
| `pipeline/src/bluebird_pipeline/gold/aggregator_season_snow_depth_days.py` | Share of days whose daily mean snow depth over `points` exceeds `threshold_cm` (needs `snow_depth_m` from the ICON season source). |
| `pipeline/src/bluebird_pipeline/gold/_season.py`, `aggregator_season_*.py` | `SeasonAggregator`s (base in `gold/base.py`): season window, point totals, `longest_episode`. |
| `pipeline/src/bluebird_pipeline/diamond/displayer_rewind.py` | `DisplayerRewind` (`schedule = "season"`): `DiamondRewind` payload per massif. |
| `pipeline/src/bluebird_pipeline/demo.py` | Synthetic weather + `build_demo()` used by `bluebird demo`. |
| `pipeline/tests/` | pytest; `_factories.py` builds Open-Meteo payloads with the real key naming. |
| `web/src/lib/config.ts` | Imports the YAML at build time; `resolveLayout()`. |
| `web/src/lib/data.ts` | Fetches `./data/diamond/<massif>/latest.json` (schema 2) and `./data/diamond/status.json` (schema 1). |
| `web/src/lib/periods.ts` | Pure: ski day, slots of the payload, labels, `expandTiles` (one tile per period), `massifView`, `nextBoundary` (tested). |
| `web/src/lib/status.ts` | Pure: footer status view (`statusView`, `worstState`, period labels), hides ended periods (tested). |
| `web/src/components/ServiceStatus.svelte`, `StaleBadge.svelte` | Footer service status; "data from HH:MM" badge on tiles with values of an earlier refresh. |
| `web/src/lib/i18n/` | `core.ts` (pure), `i18n.svelte.ts` (reactive store), `fr.json`, `en.json`. |
| `web/src/lib/generated/` | **Generated** TS types (`npm run gen:types`). Never edit by hand. |
| `web/src/tiles/registry.ts` | Tile type id → Svelte component (`xyz` → `TileXyz.svelte`, tested). |
| `web/src/tiles/TileBanner.svelte` | Type `banner`: banner (photo or illustration), top stations as odds buttons, "see all". |
| `web/src/tiles/TileBannerFull.svelte` | Type `banner_full`: photo or illustration fills the card behind title and odds. |
| `web/src/tiles/TileSimple.svelte` | Type `simple`: banner tile without banner (title without icon, odds, "see all"), shorter (`--tile-simple-h`), for KPIs lower on the page. |
| `web/src/lib/kpiView.ts` | **One view of a KPI for every tile**: `liveView` (probabilities, confidence, details) / `historicalView` (Rewind values, bars vs best), `viewFor()` (App), `itemLabel`, `rewindOfKpi`. Tiles never read payloads directly. |
| `web/src/tiles/tileModel.ts`, `OddsRow.svelte`, `RankingMore.svelte`, `StationRow.svelte`, `summary.ts` | Shared by every tile type and both kinds: top/rest, photo, odds/details (live only), empty message, badge, theme (`TILE_THEMES`, from the Rewind's filter). Odds buttons show reliability dots for live KPIs; the open list has a "see less" button at its top and bottom. |
| `web/src/tiles/TileBadge.svelte`, `web/src/components/ValuePill.svelte` | Corner badge ("REWIND 25/26") and the value pill of ranking rows ("82 %", "4,43 m"). |
| `web/src/components/ConfidenceDots.svelte` | Three reliability dots for a `confidence` level; colours via `--dot-on` / `--dot-off`. Used by odds buttons, station rows, station details, tile back. |
| `web/src/tiles/FlipCard.svelte`, `KpiBack.svelte` | Two-sided card of every tile; front = banner, title, odds (no description); back = one section each for description, time window, method, reliability, update, sources, photo credit (never on the front). |
| `web/src/lib/transitions.ts` | `arrive` / `leave` tile transitions, `rise` for sheets, and `motion()` (reduced-motion aware). |
| `web/src/lib/photos.ts`, `web/src/assets/photos/` | Banner photos `<massif>/<station_id>/<station_id>_<n>.*` (`photo: leader` draws one at random per page load; also `none` / `<path>`) and `credits.yaml`. |
| `web/src/components/AppMenu.svelte`, `FilterBar.svelte`, `Logo.svelte` | Side menu (language; blur, scroll lock, inert page), scrollable chip bar (`size` `large` = massif bar, `small` = filter bar), text-only wordmark. |
| `web/src/components/Sheet.svelte`, `web/src/lib/sheets.svelte.ts` | Generic full-window sheet (Liquid Glass, close ×, rises from the bottom) and its router (`#<id>` in the URL, back gesture closes). Reuse them for any future over-page. |
| `web/src/components/InfoPage.svelte`, `AppFooter.svelte` | A `pages.yaml` page in a `Sheet` (blocks `data_sources`, `photo_credits`); footer with the GitHub logo and page links. |
| `web/src/components/ForecastStatus.svelte` | Plain text above the tiles: data date (day of `generated_at` in the massif timezone) and update time; with a Rewind filter, the season period. |
| `web/src/tiles/TileRanking.svelte` | Type `ranking`: compact list (wrapped in `TileShell`). |
| `web/src/tiles/StationRow.svelte`, `StationDetails.svelte` | Shared station row (rank, name + reliability dots, bar, pill) and details panel. With `details` false (default) rows and odds boxes are static `div`s with `data-no-flip`. |
| `web/src/components/BannerArt.svelte` | Static SVG banner scenes (`snowfall`, `piste`, `offpiste`, `mountain`). |
| `web/src/lib/ranking.ts` | Pure ranking helpers: `sharedWindow`, `splitTop`, `reliability`. |
| `web/src/styles/` | `tokens.css` (role colour tokens, light/dark), `base.css` (page, `.card` frame), `glass.css` (header only). |
| `web/public/data/diamond/` | Demo data for local dev only, produced by `uv run bluebird demo`. |
| `scripts/ci/publish-gh-pages.sh` | The only way anything is written to `gh-pages` (used by workflows). |
| `scripts/ci/fetch-gh-pages-data.sh` | Read-only: restores published `data/` (gold, diamond) into a storage folder for the fallback and the status. |
| `.github/actions/setup-pipeline/` | Composite action: setup-uv, `uv sync --locked --no-dev`, `BLUEBIRD_DATA_DIR`, `UV_NO_SYNC=1`. |
| `scripts/setup-github.sh` | One-time GitHub setup, run by the human owner. |
| `.github/workflows/` | `ci.yml`, `deploy.yml`, `refresh.yml` (plan → bronze[source] → silver[source] → gold[KPI] → diamond[massif] → status → publish), `reference.yml`, `guard-gh-pages.yml`. |

## 3. Data flow and layers

```
sources ──Extractor──▶ bronze ──Transformer──▶ silver ──Aggregator──▶ gold ──Displayer──▶ diamond ──▶ site
```

| Layer | Class prefix | Folder | Format | Storage key |
|---|---|---|---|---|
| bronze | `Extractor` | `bronze/` | gzip JSON (raw, immutable) | `bronze/{source}/{date}/{run_id}.json.gz` |
| silver | `Transformer` | `silver/` | Parquet, canonical units | `silver/{dataset}/date={date}/{run_id}.parquet` |
| gold | `Aggregator` | `gold/` | Parquet, one row per station × period, one file per KPI | `gold/kpis/date={ski_day}/{kpi_id}.parquet` |
| diamond | `Displayer` + status step | `diamond/` | minified JSON | `diamond/{massif}/latest.json`, `.../{ski_day}.json`, `diamond/manifest.json`, `diamond/status.json` |

Silver datasets today: `ensemble_hourly` (station, band, model, member, hour),
`forecast_hourly` (same schema, member 0), `domain_features` (OSM pistes/lifts
with `coordinates`).

**Three kinds of data:**

| Kind | Examples | Fetched | Stored | Read with |
|---|---|---|---|---|
| Configuration | positions, elevations, grooming times | never (hand-written) | `config/*.yaml` | `ctx.config`, `ctx.stations()` |
| Reference | pistes, lifts (`domain_features`) | once a season, `bluebird reference` | `config/reference/` (committed, PR-reviewed) | `ctx.reference(dataset)` (any date) |
| Daily | weather (`ensemble_hourly`, `forecast_hourly`) | every refresh (6 h) | by ski day in storage | `ctx.silver(dataset)` (run date only) |
| Season archive | a closed season hour by hour (`season_hourly`) | once, after the season, `bluebird rewind` | `config/rewind/<id>/` (committed, PR-reviewed) | `rewind.load_season()` → `SeasonAggregator.aggregate(ctx, rewind, hourly)` |

Production storage: bronze and silver are temporary (7-day workflow
artifacts, one per source/dataset); gold, diamond and status are committed by
the `publish` job of `refresh.yml` to `gh-pages/data/`; reference files are
committed to `main` through a pull request. Jobs restore the published data
with `scripts/ci/fetch-gh-pages-data.sh` before computing (fallback).

## 4. Invariants (do not break)

1. **Naming convention.** Plugin class `{Prefix}{Name}` in file
   `{layer}/{prefix}_{name}.py`, prefixes `Extractor`, `Transformer`,
   `Aggregator`, `Displayer`. Registered with `@register_extractor("id")` etc.
   A test enforces it. Helper modules start with `_` and are not autodiscovered.
2. **Bronze is raw.** Extractors never transform payloads. Parsing belongs in silver.
3. **Silver is canonical.** UTC `time_utc`, m, °C, mm, cm (snow), km/h. Every
   transformer returns `self.conform(frame)`.
4. **Hourly windows are `(start, end]`.** Open-Meteo values describe the hour
   ending at their timestamp. Use `gold/_ensemble.member_window`, which also
   drops members with missing hours.
5. **Times.** Station times in YAML are local `HH:MM` in the massif timezone.
   Convert with `RunContext.local_datetime`; do timedelta arithmetic in UTC.
   `grooming_end > lifts_open` means the previous evening.
6. **Probabilities** are floats in [0, 1]; build results with
   `Aggregator.result()` so confidence and metadata are consistent. Bump an
   aggregator's `version` when its maths change.
7. **The diamond contract** is `diamond/models.py`. After changing it (or any
   config model): `uv run bluebird schemas`, then `cd web && npm run gen:types`,
   commit both, and bump `schema_version` for breaking changes (the frontend
   refuses unknown versions).
8. **Labels live in config.** KPI, tile, massif and driver labels are
   `{fr, en}` objects in YAML. UI chrome strings live in
   `web/src/lib/i18n/{fr,en}.json` with identical keys (tested).
9. **Configuration is strict.** Unknown YAML keys are errors. Plugin `Params`
   models use `extra="forbid"`. Run `uv run bluebird validate` after edits.
10. **Never fetch live data for a past date.** (Rewinds fetch an *archive*
    of a closed season through `schedule: season` sources, never a live
    forecast.) The CLI refuses `--date` with the
    bronze layer; keep it that way.
11. **Frontend uses relative URLs** (`base: './'`) so it works under any Pages path.
12. **Accessibility.** Keep `prefers-reduced-motion` / `prefers-reduced-transparency`
    handling, ≥ 4.5:1 text contrast (text uses `--ink*`, `--pill-*`,
    `--status-*`; `--prob-*` colours are for bars only), real `<button>`s with
    `aria-*` state.
13. **Reference data is never fetched by the daily run.** Sources with
    `schedule: reference` are refused by `bluebird run`; they are refreshed by
    `bluebird reference`, which never overwrites a file when the fetch fails or
    a massif has no rows. Their Transformer output must be deterministic so
    refresh diffs stay reviewable. Read them with `ctx.reference()`, never
    `ctx.silver()`.
14. **Sober design.** Components use role tokens from `tokens.css`, never raw
    colours. No background animation; the page background stays plain.
15. **Fonts and photos are self-hosted.** Fonts come from `@fontsource`
    packages, never a CDN. Every photo needs publication rights and a
    `credits.yaml` entry; never commit a photo without them.
16. **Equal tiles, two faces.** Banner tiles keep the same collapsed size
    (`--tile-*` tokens in `base.css`), `simple` tiles the shorter
    `--tile-simple-h`; a new tile type uses one of these sizes or adds its own token, shared by
    all its tiles. Every tile is a
    `FlipCard`; interactive content inside a tile must be a real button/link or
    carry `data-no-flip`, otherwise a tap on it flips the card. The `.card`
    frame (striped corners) belongs to each face, never to the static wrapper,
    so it rotates with the card.
17. **KPI method text** uses only `{param}` placeholders that exist in the
    KPI `params` (`bluebird validate` checks it), so the explanation on the
    tile back always matches the maths.
18. **Live and historical stay apart.** KPIs have `kind: live | historical`.
    The daily run (`run_gold`, `DisplayerMassifDaily`) only uses
    `enabled_kpis(kind="live")` and `schedule = "daily"` displayers; sources
    with `schedule: season` are refused by `bluebird run`. Historical KPIs use
    `SeasonAggregator`s (checked against the KPI kind by `bluebird validate`)
    and are only computed by `bluebird rewind`, which refuses a season that is
    not over. `config/rewind/` is generated and committed, never hand-edited.
    "All" never shows the tiles of an `exclusive` filter. On the site, tiles
    only read a `KpiView` (`lib/kpiView.ts`) and colours only change through
    tile themes (token overrides, `[data-tile-theme]`): no tile type, prop or
    CSS is specific to one kind of KPI or one Rewind.
19. **One request per source and refresh.** Extractors of APIs that accept
    several locations send one grouped request (`bronze/_open_meteo.py`);
    bronze records list their `locations`. Silver still reads the older
    one-record-per-station batches.
20. **Ski day and periods.** `run_date` is the ski day (starts at
    `day_start`, 06:00 local). Aggregators implement `compute(ctx, ref,
    period)`; the base class only computes periods **not over** at
    `generated_at`. Period instance key: `period_id@ski_day`. Time slots in
    `periods.yaml` must tile the ski day (validated). A period is shown until
    its end, by the pipeline (published periods) and by the site (clock).
21. **Tiles are templates.** A tile title must contain `{period}`; the site
    expands each tile into one instance per period with a unique DOM id
    (`<tile>--<period>-<ski_day>`); its `KpiView` is built for that period
    (`liveView(kpi, payload, slot)`, `stale` when the values are older than
    the payload). Tiles of historical KPIs have no `{period}` and are shown
    once.
22. **Fallback, never silence.** A KPI that cannot be recomputed keeps the
    rows of its latest run for periods still to come (`read_gold`, original
    `generated_at`), shown as stale. Every unit reports a state; a missing CI
    report counts as `down`. `diamond/status.json` is built once per refresh
    after every massif payload (`bluebird status`).
23. **CI jobs share the run id** chosen by `plan` (`--run-id`); never compute
    dates from each job's own clock. `--run-id` older than 3 h is refused
    with the bronze layer.

## 5. Git rules for agents

Summary of AGENTS.md §3, which is authoritative.

- `main` is the **only long-lived branch** (and the default branch). There is
  no `dev` branch.
- Work on a **short-lived branch** created from `main` (`feat/<topic>`,
  `fix/<topic>`, `docs/<topic>`). **Never push to `main` or `gh-pages`**; never
  force-push. Rulesets block it anyway.
- Changes reach `main` only through a pull request with the `CI result` check
  green. Merging triggers the deploy. Delete the branch after merge.
- `gh-pages` is written exclusively by `deploy.yml` / `refresh.yml` (its `publish` job) through
  `scripts/ci/publish-gh-pages.sh`. Do not open PRs against it.
- Never commit `/data`, `.venv`, `node_modules`, `web/dist`.
- Commit or push only when the human asks. Commit messages in English.

## 6. Commands

```bash
# Pipeline (from pipeline/)
uv sync
uv run bluebird validate            # config + plugin checks
uv run bluebird schemas [--check]   # regenerate / verify config/schemas
uv run bluebird plugins             # list registered plugins
uv run bluebird run [--layer L] [--massif M] [--source S] [--kpi K] [--run-id ID]
                    [--report R.json] [--export DIR] [--data-dir D] [--strict]
uv run bluebird plan [--json] [--run-id ID]   # units of a refresh (CI matrices)
uv run bluebird status --reports DIR [--run-id ID] [--summary FILE] [--export DIR]
uv run bluebird reference [--massif M] [--source S] [--no-fetch]   # pistes/lifts → config/reference
uv run bluebird rewind --rewind 2025-26 [--massif M] [--source S] [--no-fetch]   # season → config/rewind
uv run bluebird demo [--now ISO]    # rebuild web/public/data/diamond (synthetic, 06:00 refresh)
uv run ruff format . && uv run ruff check .
uv run pytest

# Web (from web/)
npm ci
npm run gen:types                   # after any schema change
npm run check                       # svelte-check, must be 0 errors 0 warnings
npm test
npm run build
npm run dev
```

## 7. Recipes (minimal file sets)

| Task | Files to touch | Then run |
|---|---|---|
| Add a station | `config/stations/<massif>.yaml` (with `short_name`), folder `web/src/assets/photos/<massif>/<id>/.gitkeep` | `bluebird reference --massif <massif>`, `bluebird validate`, `npm test` |
| Add a massif | `config/massifs.yaml`, new `config/stations/<id>.yaml`, optional `layout.yaml` override | `bluebird reference --massif <id>`, `bluebird validate`, `bluebird demo` |
| Add reference data | `bronze/extractor_<x>.py`, `silver/transformer_<x>.py` with `reference_suffix`, `reference_file`, `read_reference`; source with `schedule: reference` | `bluebird reference`, `pytest`, commit `config/reference/` |
| Add a source | `bronze/extractor_<x>.py` (one grouped request if the API allows), `silver/transformer_<x>.py`, `config/sources.yaml` (+ attribution), tests | `bluebird validate`, `pytest` |
| Add a KPI | `gold/aggregator_<x>.py` (live: `compute(ctx, ref, period)`), PROJECT.md "Available indicators", README.md "Tiles on the site", `config/kpis.yaml` (name, description, `method` with `{param}` placeholders, params, drivers, filters, `periods` for live KPIs), `config/tiles.yaml` (live: title with `{period}`), `config/layout.yaml`, tests | `bluebird validate`, `pytest`, `bluebird demo` |
| Add a period | `config/periods.yaml` (slot + labels per day; keep slots tiling the day), `periods` of the KPIs | `bluebird validate`, `pytest`, `bluebird demo` |
| Add a tile type | README.md "Tiles on the site" when used, `web/src/tiles/Tile<Xyz>.svelte`, `web/src/tiles/registry.ts` (id `xyz` + `skeletonVariant`), `config/tiles.yaml` | `npm run check`, `npm test`, 390 px screenshots |
| Change the diamond shape | `diamond/models.py`, displayer, frontend usage | `bluebird schemas`, `npm run gen:types`, `bluebird demo`, all tests |
| Reorder tiles | `config/layout.yaml`, README.md "Tiles on the site" | `bluebird validate`, `npm test` |
| Add a filter | `config/filters.yaml`, `filters: [id]` on KPIs in `config/kpis.yaml` | `bluebird validate`, `bluebird schemas`, `npm test` |
| Add a banner photo | `web/src/assets/photos/<path>.webp`, `credits.yaml`, tile `photo` option | `npm run build`, 390 px screenshots |
| Add a page | `config/pages.yaml` (`pages[]`, optional `footer.pages`) | `bluebird validate`, `npm test`, 390 px screenshots |
| Add another kind of over-page | content inside `components/Sheet.svelte`, opened with `sheets.open(id)` (`lib/sheets.svelte.ts`) | `npm run check`, `npm test` |
| Add a Rewind | `config/rewinds.yaml`, exclusive filter (`theme: rewind`) after `all` in `filters.yaml`, KPI tags, tiles of any type + layout (Rewind and theme come from the KPI) | after the season: `bluebird rewind --rewind <id>`, review and commit `config/rewind/<id>/` |
| Add a historical KPI | `gold/aggregator_season_<x>.py` (`SeasonAggregator`, value in its native unit), `kpis.yaml` (`kind: historical`, `value {unit, decimals, scale, max}` — snow totals use `m` with `scale: 0.01`, percentages `%` with `scale: 100, max: 100`; method, drivers, filter), PROJECT.md "Available indicators", README.md "Tiles on the site", Rewind `kpis`, tile + layout, tests | `bluebird validate`, `pytest`, `bluebird rewind --no-fetch` |
| Add a UI string | `web/src/lib/i18n/fr.json` **and** `en.json` | `npm test` |

## 8. Pitfalls already met

- **iCloud folder.** The repo may live in iCloud Drive. iCloud marks files in
  `.venv` hidden, and Python ≥ 3.13 ignores hidden `.pth` files →
  `ModuleNotFoundError: bluebird_pipeline`. Use
  `UV_PROJECT_ENVIRONMENT=<path outside iCloud>`.
- **Open-Meteo series names.** `{var}[_memberNN][_{model_suffix}]`; the suffix
  differs from the requested model (`ecmwf_ifs025` → `ecmwf_ifs025_ensemble`,
  `icon_seamless` → `icon_seamless_eps`) and is absent when only one model is
  requested. Control run = member 0. `freezing_level_height` is null for these
  ensemble models and for `meteofrance_seamless`; do not build KPIs on it.
- **Open-Meteo rate limits.** Ensemble calls are weighted by members. The
  extractor waits on 429 (`rate_limit_wait_s`) and spaces calls
  (`min_interval_s`). Don't add bands/days/variables the KPIs don't use.
- **Overpass** (OSM) is slow and returns 429/504 often: reference source only.
  Features are selected within 4 km of each station, so neighbours share
  features and big domains are under-counted (Saint-Lary ≈ 12 km found). Do not
  show these totals as official figures; selecting by `landuse=winter_sports`
  areas is the planned fix.
- **YAML flow mappings.** `{ fr: Neige, scénario haut }` splits on the comma.
  Quote such values or use a dash.
- **SVG and CSS variables.** `var()` does not work in SVG presentation
  attributes (`fill="var(--x)"`); use `style="fill: var(--x)"`.
- **SVG gradient ids.** Several inline SVGs on one page share the document's id
  space; a fixed `id="sky"` makes every banner use the first one. Prefix ids
  with `$props.id()` (see `BannerArt.svelte`).
- **Graphics on the odds buttons.** `--track` is almost the colour of
  `--pill-bg`, so empty reliability dots drawn with it vanish on the
  light-blue buttons. `OddsRow` sets `--dot-off` to a mix of `currentColor`
  (and `--dot-on: currentColor` when pressed); do the same for any new mark
  drawn on a pill.
- **`inert` blurs the opener.** App makes the page `inert` in the same update
  that renders a sheet, so `document.activeElement` read in the sheet's
  `$effect` is already `<body>` and focus cannot return to the footer link.
  Capture the opener in `$effect.pre` (see `Sheet.svelte`).
- **Headless virtual time and sheets.** Like tiles, a closed `Sheet` stays in
  the DOM under `--virtual-time-budget` (its `out:` transition never ends).
  Check opening and closing with the DevTools protocol in real time.
- **Open-Meteo weighting of long ranges.** The archive counts a request of more
  than two weeks per location as several calls (~11 per point for a
  five-month season). Keep `min_interval_s` high on season sources and few
  points per station; a Pyrenees Rewind is ~3,400 weighted calls.
- **Multi-location `elevation`.** With several coordinates, `elevation` must
  list one value per point, and `nan` disables downscaling. That is why the
  season extractor sends the station point (with elevation) and the area
  points (none: terrain height) in two separate requests.
- **YAML dates become `Date` objects in the site.** `@rollup/plugin-yaml`
  parses `start: 2025-12-01` as a JavaScript `Date`, while the generated types
  say `string`; string code (`split`) then throws during render and the page
  silently keeps the previous tiles. Normalise with `isoDate()` when loading
  (see `enabledRewinds` in `web/src/lib/config.ts`), or quote dates in YAML.
- **No snow depth in the AROME archive.** `meteofrance_seamless` returns
  `snow_depth` as all nulls (unit `undefined`); `icon_seamless` has it (~7 km,
  not downscaled), `ecmwf_ifs025` is near zero at its grid height. Snow depth
  therefore comes from a second season source (`open_meteo_historical_snowpack`).
- **Several season sources share one hourly file.** Read it once per file (see
  `load_season`), not once per source, or every value is counted twice; merge
  by `model` when fetching only some sources.
- **No visibility, no fog code, misleading sunshine.** The AROME archive
  returns `visibility` as nulls and never emits fog codes (45/48), and
  `sunshine_duration` counts more than half an hour of sun in most hours of
  steady snowfall. White days use humidity, low cloud, snowfall and radiation
  vs a clear sky instead. The ICON ensemble has no `cloud_cover_low` (unit
  `undefined`): fall back to total cloud cover.
- **Two season sources of the same model** must merge by column
  (`rewind.merge_columns`), never by model, or the second fetch deletes the
  first one's values.
- **KPI descriptions are not interpolated.** Only `method` gets its `{param}`
  values; a placeholder in `description` would show raw on the tile back.
  `bluebird validate` now rejects it.
- **Aware datetimes in polars filters.** Comparing a `Datetime(UTC)` column
  with a Europe/Paris datetime raises a `SchemaError`: convert bounds with
  `.astimezone(UTC)` first (see `gold/_season.in_window`).
- **Variable named `window`** in a component shadows the global object; use
  another name (`timeWindow`).
- **TypeScript is pinned to 6.x.** svelte-check does not support TypeScript 7
  alone yet.
- **Headless Chrome** enforces a ~500 px minimum window width; screenshot the
  site inside a 390 px iframe to check mobile layout.
- **Headless Chrome virtual time** (`--virtual-time-budget`) never completes
  Svelte `out:` transitions: leaving elements stay in the DOM and filters look
  broken. Test transitions in real time by driving Chrome through the DevTools
  protocol (`--remote-debugging-port`, `Runtime.evaluate` from a Node script).
- **Generated files** (`config/schemas`, `web/src/lib/generated`) are checked
  in CI; regenerate rather than hand-edit. `config/rewind/` is regenerated
  with `bluebird rewind` (`--no-fetch` when only the maths changed).
- **GitHub cron is UTC.** Paris changes offset twice a year. `refresh.yml`
  has one cron line per offset and the `plan` job keeps the line matching
  `TZ=Europe/Paris date +%z` (compare with `github.event.schedule`).
- **Open-Meteo grouped requests** still count every location in the
  weighted quota: grouping saves HTTP requests, not quota.
- **`uv run` re-syncs dev dependencies** after `uv sync --no-dev`; CI sets
  `UV_NO_SYNC=1` (composite action).
- **Matrix jobs with `if: false`.** Give plan outputs a `'[]'` default so
  `fromJSON` never sees an empty string.
- **Several tile instances share a tile config.** Use the instance id for DOM
  ids (`aria-labelledby`), never the configured tile id.
- **Grid items widen with `white-space: nowrap`.** Long tile titles pushed the
  odds buttons out of the card: banner contents use
  `grid-template-columns: minmax(0, 1fr)` and long titles get a smaller font
  clamped to two lines.
- **Schema bump vs published data.** After merging a diamond
  `schema_version` change, the deployed site rejects the old `latest.json`
  until the next refresh: run `Data refresh` manually.
- **Ski day vs `--date`.** A context created at 05:30 local belongs to the
  previous ski day; tests mixing an explicit `run_date` with another `now`
  must not expect CLI jobs (which derive the date from `--run-id`) to agree.
- **GitHub default branch.** GitHub makes the first pushed branch the default.
  `git push` cannot change it, and GitHub refuses to delete the default branch.
  Change it in Settings → General or with
  `gh repo edit <owner>/<repo> --default-branch main` (`setup-github.sh` does it).

## 9. Definition of done

A change is done when all of these pass locally:

```bash
cd pipeline && uv run ruff format --check . && uv run ruff check . \
  && uv run bluebird validate && uv run bluebird schemas --check && uv run pytest
cd ../web && npm run gen:types && git diff --exit-code -- src/lib/generated \
  && npm run check && npm test && npm run build
```

…and, for UI changes, the page was looked at on a 390 px wide viewport in
light and dark mode, in French and English. Update README.md, PROJECT.md and
this file when behaviour, commands or conventions change.

## 10. Roadmap context

Reference pistes/lifts are used by the Rewind (domain and off-piste
sampling points) but not by any live KPI or tile yet. Future KPIs (live,
Rewind, All Time) are listed in PROJECT.md "Future indicators"; future
features, their feasibility and the planned tile ordering algorithm
(`rankTiles`, `ordering` in `layout.yaml`) in README.md "Future features".
Periods are ready for longer horizons: weekend and week periods (needs
`horizon_days`/period kinds beyond today and tomorrow, and more forecast
days), and "Aujourd'hui / Demain" filter chips to shorten the page.
For the sunniest resort, use the stored `shortwave_wm2`, not `sunshine_s`
(see §8). Planned next (see PROJECT.md): Météo-France avalanche bulletin (BRA, needs an
API key), resort opening status (scraper), slope/aspect from an IGN or
Copernicus elevation model, 7-day trend tile, map tile using
`domain_features`, more massifs (Alps), probability calibration against
observed snow using the gold history.
