# CONTEXT.md — briefing for AI coding assistants

Read this file before changing anything in the repository. It states what
Bluebird is, how the code is organised, the invariants you must keep, and the
exact commands that prove a change works. Human-oriented docs:
[README.md](README.md) (developers), [PROJECT.md](PROJECT.md) (product) and
[TILES.md](TILES.md) (tile axes and inventory).

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
- First massif: Pyrenees, 18 stations. 19 **live** KPIs (probabilities per
  period), one category filter each (the indicator categories of
  PROJECT.md): `snow` (Neige: `snowfall_chance`, `powder_alert_chance`,
  `snowmaking_chance`), `snow-quality` (Glisse: `onpiste_powder_chance`,
  `offpiste_powder_chance`, `spring_snow_chance`, `hard_snow_chance`,
  `heavy_snow_chance`, `easy_conditions_chance`), `sky` (Ciel:
  `whiteout_chance`, `bluebird_day_chance`, `sunset_chance`,
  `starry_night_chance`, `sunny_slot_chance`), `comfort` (Confort:
  `mild_day_chance`, `wind_chill_chance`), `access` (Accès: `chains_chance`,
  `lift_wind_chance`), `safety` (Sécurité: `wind_slab_chance`). All use only
  the data already fetched (ensemble mid/summit). Each is shown after its
  `display` (`kpis.yaml`): `value` (median of a driver: snow, snow alert,
  snowmaking, on-piste powder, full sun, wind chill, lift wind), `levels`
  (Oui / Possible / Non: chains, hard snow, wind slab) or `percent` (the
  others; sunset with its time as `note`).
- **Rewinds** review a closed season with **historical** KPIs (values, not
  probabilities), built once by `bluebird rewind`. First instance: *Rewind
  25/26* (2025-12-01 → 2026-05-01, Pyrenees): `season_total_snowfall`,
  `season_longest_snowfall`, `season_domain_snowfall`, `season_offpiste_snowfall`,
  `season_deep_snow_days` (% of days with > 70 cm on average over the slopes,
  ICON snow depth), `season_white_days` (fewest first, `order: asc`). The info
  line above the tiles reads "Saison 2025/2026". Shown only under its
  Christmas-red filter, the first level-1 chip (no levels, never on the home page). Rewind tiles are not split by period.
- The UI mimics a sports-betting page: one tile per live KPI and period (tile
  templates in `tiles.yaml` are expanded per period, "Neige {period}"),
  stations ranked by descending probability. A tile disappears when its
  period ends. Tiles are classified on three axes in `tiles.yaml`: `scope`
  (`ranking` today; `station`, one resort, planned), `format` (`full`,
  `banner`, `compact`) and `visual` (`scene`, `photo`; `webcam` as a
  background planned); live or Rewind comes from the KPI `kind`. A tile
  `webcam` rule (first scope: bluebird day + summit webcam, Cauterets) shows a
  red LIVE badge linking the leading station's webcam page (Skaping) while
  today's period is in progress; the image is never shown (rights). A full-window page (`#status`, linked from the footer) shows the service status of the last refresh. Style: design "Nuit étoilée" (TILES.md §9, the
  reference for any tile design): betting-app layout in midnight blue and
  electric blue, glass cards, odds buttons and chips (Liquid Glass, opaque
  fallback), radius 24px, no stripes, sober plain background, no background
  animation; font Sora (`@fontsource-variable/sora`: titles and values 700,
  text 400–600) and Barlow Semi Condensed ExtraBold Italic for the logo
  wordmark only (`--font-logo`), self-hosted and imported in `main.ts`.
  `full` tiles show their image down to the bottom of the card, under the
  "see all" bar.
  Header: logo left (ski goggle mark, lens gradient by phase of the day,
  then the "Bluebird" wordmark); on the right the appearance button (icon of
  the choice: System by default, Light, Dark; `lib/theme.ts`) then the flag
  of the current language (default language from the browser), both opening
  the same kind of popup (`ChoicePopup.svelte`); while the page
  scrolls down, the two chip bars below fold into one row recalling the
  chosen place and filter (two pills max, `lib/compactHeader.ts`), back on
  scroll up or tap;
  below, the massif bar (place levels of `lib/geoLevels.ts`:
  massif → zone = département or foreign country/region (`zones` of
  `massifs.yaml`, one mixed list: French zones first, foreign ones after
  with a flag; Spain by comunidad autónoma) → linked ski area (`domains` of
  the stations file, two stations or more); the chosen place restricts every
  ranking; resorts abroad get a flag in their short name) then
  the filter bar (same chips, Spotify-style **filter levels**: level 1 =
  topics of `filters.yaml`; a chosen chip is filled with a ×, leads the row
  and hides its siblings, then the next level appears: `group`
  (sub-categories, skipped when single), `day` (Aujourd'hui, Demain) then
  `slot` (Matin…Nuit), at most 4 levels; above the slot level only
  day-grain tiles are shown, time-slot tiles only once a slot is chosen;
  no "All": with nothing
  chosen the home page shows the `home` tiles of `layout.yaml`, in priority
  order: bluebird day today first). Above the tiles, plain text (no card): data date (day of
  `generated_at`) and update time. Station details on tap are off for now
  (tile option `details`, default false): the tiles show the probability only.
- UI languages: French (default), English and Spanish (`LOCALES` in
  `web/src/lib/i18n/core.ts`). **All code, comments, docs and commit
  messages are in English.** User-facing strings exist in all three.
- Hosting and storage: **GitHub only** (Pages + the `gh-pages` branch). No
  server, no database, no cloud bucket.

## 2. Repository map

| Path | Role |
|---|---|
| `AGENTS.md` | Mandatory rules for AI agents, applied on every prompt. |
| `TILES.md`, `docs/tiles/render.mjs`, `docs/tiles/*.svg` | The tile axes (scope, format, visual, kind), corner badges, fields and the inventory of every tile, with one mockup per value. Kept up to date with every tile change (AGENTS.md §1); the inventory and totals are checked by `web/src/lib/tilesDoc.test.ts`. The SVGs are **generated** by `node docs/tiles/render.mjs` (same mockup and example data for all; edit the script, never the SVGs). |
| `CLAUDE.md` | Imports `AGENTS.md` and `CONTEXT.md` for Claude Code. |
| `config/filters.yaml` | Level-1 chips of the filter bar, their `levels` (`group`, `day`, `slot`) and sub-categories `groups` (every KPI of a filter in exactly one); KPIs opt in with `filters: [id]` in `kpis.yaml`. Chip labels of the levels: `days` and period `chip` in `periods.yaml`. |
| `config/periods.yaml` | `day_start` (06:00), `horizon_days`, periods (time slots covering the ski day + `day` with `native_window`) and their labels per day. Day-grain periods (`native_window`): `day`, `sunset` (06:00–22:00), `overnight` (06:00 → 06:00). |
| `config/rewinds.yaml` | Rewinds: season `start`/`end` (local days, included), massifs, historical KPIs, its level-1 filter (no levels). |
| `config/rewind/<id>/<massif>.hourly.parquet`, `.json` | **Generated** by `bluebird rewind`, committed via PR: the season hour by hour (silver `season_hourly`) and the ranked payload the site bundles. Never edit by hand. |
| `config/pages.yaml` | Footer (GitHub repository link, page links) and full-window pages (about, legal notice, privacy) with `{fr, en, es}` sections and built-in blocks. |
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
| `pipeline/src/bluebird_pipeline/gold/_whiteout.py`, `aggregator_whiteout_chance.py`, `aggregator_season_white_days.py` | White days: `SkiHours` (ski hours params; also the day-grain window of the KPIs with time slots, `day_or_slot`), `WhiteoutRule` (params shared by both KPIs), clear-sky radiation (`clear_sky_expr`), white hour rule; live probability (period `day`: today and tomorrow) and season count. |
| `pipeline/src/bluebird_pipeline/gold/_conditions.py`, `aggregator_{powder_alert,snowmaking,spring_snow,hard_snow,heavy_snow,easy_conditions,sunset,starry_night,sunny_slot,wind_chill,mild_day,chains,lift_wind,wind_slab}_chance.py` | Condition KPIs from the fetched ensemble: `member_table` + `share` (`_ensemble.py`); helpers wet bulb (snowmaking), wind chill, lapse-rate temperature (chains: road at the base elevation), `sunset_utc` (period `sunset`, native window 06:00–22:00). Tested in `tests/gold/test_live_conditions.py`. |
| `pipeline/src/bluebird_pipeline/gold/aggregator_bluebird_day_chance.py` | Bluebird day: fresh snow over `lookback_hours` before `ski_start`, then ≥ `min_sunny_hours` sunny ski hours (`sunny_hour_expr`: total cloud and radiation vs clear sky). Period `day` only. |
| `pipeline/src/bluebird_pipeline/gold/aggregator_season_snow_depth_days.py` | Share of days whose daily mean snow depth over `points` exceeds `threshold_cm` (needs `snow_depth_m` from the ICON season source). |
| `pipeline/src/bluebird_pipeline/gold/_season.py`, `aggregator_season_*.py` | `SeasonAggregator`s (base in `gold/base.py`): season window, point totals, `longest_episode`. |
| `pipeline/src/bluebird_pipeline/diamond/displayer_rewind.py` | `DisplayerRewind` (`schedule = "season"`): `DiamondRewind` payload per massif. |
| `pipeline/src/bluebird_pipeline/demo.py` | Synthetic weather + `build_demo()` used by `bluebird demo`. |
| `pipeline/tests/` | pytest; `_factories.py` builds Open-Meteo payloads with the real key naming. |
| `web/src/lib/config.ts` | Imports the YAML at build time; `resolveLayout()`. |
| `web/src/lib/data.ts` | Fetches `./data/diamond/<massif>/latest.json` (schema 2) and `./data/diamond/status.json` (schema 1). |
| `web/src/lib/periods.ts` | Pure: ski day, slots of the payload, labels, `expandTiles` (one tile per period), `massifView`, `nextBoundary` (tested). |
| `web/src/lib/status.ts` | Pure: service status view (`statusView`, `worstState`, period labels), hides ended periods (tested). |
| `web/src/components/ServiceStatus.svelte`, `StaleBadge.svelte` | `service_*` blocks of the "Service status" page (`config/pages.yaml`, rendered by `InfoPage`); "data from HH:MM" badge on tiles with values of an earlier refresh. |
| `web/src/lib/i18n/` | `core.ts` (pure: `LOCALES`, `LOCALE_NAMES`, `LOCALE_FLAGS`, `localizedFrom`, `sameInAll`), `i18n.svelte.ts` (reactive store), `fr.json`, `en.json`, `es.json`. |
| `web/src/lib/generated/` | **Generated** TS types (`npm run gen:types`). Never edit by hand. |
| `web/src/tiles/registry.ts` | Tile `format` → Svelte component (`xyz` → `TileXyz.svelte`, tested), `skeletonVariant`, `tileRows`, `TileProps` (with the optional `webcam`). |
| `web/src/tiles/TileBanner.svelte` | Type `banner`: banner (photo or illustration), top stations as odds buttons, "see all". |
| `web/src/tiles/TileFull.svelte` | Format `full`: photo or illustration fills the card behind title and odds. |
| `web/src/tiles/TileCompact.svelte` | Format `compact`: banner tile without image (title without icon, compact odds, "see all"), half a banner tile (`--tile-compact-h`), so two stack beside a banner tile on wide screens. |
| `web/src/lib/webcams.ts`, `web/src/components/WebcamBadge.svelte` | Pure, tested: `liveWebcam(tile, view, now, stationWebcams)` (tile `webcam` rule: period in progress, leading station's webcam at one of `positions`, probability ≥ `min_probability`); the LIVE badge, a real `<a>` (new tab) in the top left corner of `full`/`banner` tiles, `--live-bg`/`--on-live` tokens. `stationWebcams` comes from `lib/config.ts` (`webcams` of the stations files). |
| `web/src/lib/kpiView.ts` | **One view of a KPI for every tile**: `liveView` (after the KPI `display`: percent, median value with band note, or levels; confidence, details) / `historicalView` (Rewind values, bars vs best), `viewFor()` (App), `itemLabel`, `rewindOfKpi`. Tiles never read payloads directly. |
| `web/src/tiles/tileModel.ts`, `OddsRow.svelte`, `RankingMore.svelte`, `StationRow.svelte`, `summary.ts` | Shared by every tile format and both kinds: top/rest, photo (`visual: photo`), odds/details (live only), empty message, badge, theme (`TILE_THEMES`, from the Rewind's filter). Odds buttons show reliability dots for live KPIs; the open list has a "see less" button at its top and bottom. |
| `web/src/tiles/TileBadge.svelte`, `web/src/components/ValuePill.svelte` | Corner badge ("REWIND 25/26") and the value pill of ranking rows ("82 %", "4,43 m"). |
| `web/src/components/ConfidenceDots.svelte` | Three reliability dots for a `confidence` level; colours via `--dot-on` / `--dot-off`. Used by odds buttons, station rows, station details, tile back. |
| `web/src/tiles/FlipCard.svelte`, `KpiBack.svelte` | Two-sided card of every tile; front = banner, title, odds (no description); back = one section each for description, time window, method, reliability, update, sources, photo credit (never on the front). |
| `web/src/lib/transitions.ts` | `arrive` / `leave` tile transitions, `rise` for sheets, and `motion()` (reduced-motion aware). |
| `web/src/lib/photos.ts`, `web/src/assets/photos/` | Banner photos `<massif>/<station_id>/<station_id>_<n>.*` (tile `visual: photo` draws one of the leading station at random per page load; `scene` = none) and `credits.yaml`. |
| `web/src/components/ChoicePopup.svelte`, `LanguagePicker.svelte`, `ThemePicker.svelte`, `Flag.svelte` | Choice popup shared by the header buttons (options with a leading snippet, check on the current one; blur, scroll lock, inert page, Escape, focus back to the opener via `$effect.pre`); language popup (flag + endonym per locale, `LOCALE_FLAGS`/`LOCALE_NAMES` in `lib/i18n/core.ts`); appearance popup (System / Light / Dark with their icons); SVG flags with `--flag-*` tokens (no emoji: Windows shows letters). |
| `web/src/lib/theme.ts`, `theme.svelte.ts` | Appearance: `THEMES` (`system` default, `light`, `dark`), `THEME_ICONS` (`sun-moon`: a sun and a moon split by a slash; `sun`, `moon`), `parseTheme`, `applyTheme` (`data-theme` on `<html>`, removed for `system`; `theme-color` metas follow a forced mode), pure and tested; reactive store `theme` (preference `theme`). `index.html` applies the stored mode before the first paint. |
| `web/src/components/AppHeader.svelte`, `web/src/lib/compactHeader.ts` | Sticky header: logo, language button, the two chip bars; compact mode: `nextScrollState` (fold after 12 px down below 96 px, open after 12 px up; anchor = lowest point while open, highest while folded) and `headerSummary` (deepest chosen place + chosen filter levels), both pure and tested; folds animate `grid-template-rows` 1fr ↔ 0fr with fade; 420 ms settle after a fold; never folds under keyboard focus (`:focus-visible` only); folded pills on one line (`minmax(0, 1fr)` column, filter pill shrinks first). |
| `web/src/components/FilterBar.svelte`, `Logo.svelte` | Scrollable chip bar, the same chips for the massif bar and the filter bar (options with `pressed`/`removable` (×), `resetScroll`, chips grow in and slide with `animate:flip`), logo (goggle mark + wordmark; phase of the day of the first massif's timezone, checked every minute). |
| `web/src/components/LogoMark.svelte`, `web/src/lib/timeOfDay.ts` | Ski goggle mark (three-quarter view): only the lens gradient changes, tokens `--logo-lens-<phase>-<1..3>` (`--logo-frame`, `--logo-glare`); pure `dayPhase(now, timezone)` (dawn 06, day 09, dusk 17, night 20), tested. |
| `web/public/favicon.svg`, `web/public/apple-touch-icon.png`, `web/scripts/apple-touch-icon.svg`, `web/scripts/make-apple-icon.sh` | Static copies of the `day` mark: favicon, and the 180 px home-screen icon rendered from its SVG source (headless Chrome + `sips`, macOS). `src/lib/brandIcons.test.ts` checks shapes, day colours and links stay in sync with `LogoMark.svelte`. |
| `web/src/lib/filterLevels.ts` | Pure, tested: `filterState(path, …)` → chips, tiles and tile instances of the filter path (home = `homeTiles`: `layout.yaml` `home` in priority order), `LEVEL_KINDS` (`group`, `day`, `slot`: options + match; a single group is skipped), `isDayGrain` (grain rule: day-grain tiles until a slot is chosen), `nextPath` (tap = choose, tap a chosen chip = remove it and the levels after). Only level 1 is stored in `localStorage`. |
| `web/src/lib/geoLevels.ts` | Pure, tested: `geoState(path, massifs, siteStations, siteDomains, fallback)` → chips of the massif bar (massif, zone skipped below two, linked area with 2+ stations), the massif shown and the station subset (`null` = all) passed to `viewFor(…, only)`; `readGeoPath` (preference `geo`, migrated from `massif`).; French zones first, foreign ones after with `flagOf` (ISO code → flag emoji). `stationCountries` (`lib/config.ts`) feeds the flag of `shortName` in `lib/kpiView.ts`. |
| `web/src/components/Sheet.svelte`, `web/src/lib/sheets.svelte.ts` | Generic full-window sheet (Liquid Glass, close ×, rises from the bottom) and its router (`#<id>` in the URL, back gesture closes). Reuse them for any future over-page. |
| `web/src/components/InfoPage.svelte`, `AppFooter.svelte` | A `pages.yaml` page in a `Sheet` (blocks `data_sources`, `photo_credits`); footer with the GitHub logo and page links. |
| `web/src/components/ForecastStatus.svelte` | Plain text above the tiles: data date (day of `generated_at` in the massif timezone) and update time; with a Rewind filter, the season period. |
| `web/src/tiles/TileShell.svelte`, `TileSkeleton.svelte` | Plain card shown in development for an unknown tile format; loading placeholder shaped like each tile format (`skeletonVariant`: full, banner, compact). |
| `web/src/tiles/StationRow.svelte`, `StationDetails.svelte` | Shared station row (rank, name + reliability dots, bar, pill) and details panel. With `details` false (default) rows and odds boxes are static `div`s with `data-no-flip`. |
| `web/src/components/BannerArt.svelte` | Static SVG banner scenes (`snowfall`, `piste`, `offpiste`, `mountain`). |
| `web/src/lib/ranking.ts` | Pure ranking helpers: `sharedWindow`, `splitTop`, `reliability`. |
| `web/src/styles/` | `tokens.css` (role colour tokens light/dark, fonts `--font-sans`/`--font-display`/`--font-logo`, `--display-weight`/`--display-tracking`, glass `--glass-edge`/`--glass-hi`/`--card-bg`, radii), `base.css` (page, `.card` glass card, tile sizes, odds glass tokens `--odds-glass`/`--odds-overlay-*`, tile themes), `glass.css` (header). Specified in TILES.md §9. |
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
6. **Probabilities** are floats in [0, 1], always computed, even for KPIs
   shown as a value or levels (`display`); a `value` display needs its
   `driver` and `range` drivers declared in `kpis.yaml` (validated), ranks
   by the value and rates reliability by the spread. Build results with
   `Aggregator.result()` so confidence and metadata are consistent. Bump an
   aggregator's `version` when its maths change.
7. **The diamond contract** is `diamond/models.py`. After changing it (or any
   config model): `uv run bluebird schemas`, then `cd web && npm run gen:types`,
   commit both, and bump `schema_version` for breaking changes (the frontend
   refuses unknown versions).
8. **Labels live in config.** KPI, tile, massif and driver labels are
   `{fr, en, es}` objects in YAML (`Localized` in `config.py`, every field
   required). UI chrome strings live in `web/src/lib/i18n/{fr,en,es}.json`
   with identical keys and placeholders (tested). Code that builds a label
   uses `localizedFrom` / `sameInAll`, never a literal `{ fr, en }`.
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
    `credits.yaml` entry; never commit a photo without them. Photos come
    from Openverse (https://openverse.org/fr) under a reusable licence
    (CC0, PDM, CC BY, CC BY-SA; never ND); photos from resort or tourism
    sites are all rights reserved unless the owner agrees.
16. **Equal tiles, two faces.** `full` and `banner` tiles keep the same collapsed size
    (`--tile-*` tokens in `base.css`), `compact` tiles the shorter
    `--tile-compact-h`, derived in `base.css` so that two compact tiles plus
    `--tile-gap` equal one banner tile (frame included); keep that formula
    when changing a tile token. On wide screens banner tiles span two grid
    rows (`tileRows`). A new tile format uses one of these sizes or adds its own
    token, shared by all its tiles. Every tile is a
    `FlipCard`; interactive content inside a tile must be a real button/link or
    carry `data-no-flip`, otherwise a tap on it flips the card. The `.card`
    glass card belongs to each face, never to the static wrapper, so it
    rotates with the card. Colours, fonts, sizes and glass recipes of a new
    tile axis, value or format follow TILES.md §9 (design "Nuit étoilée").
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
    Rewind tiles only show under their Rewind filter (never on the home
    page, whose tiles are the live `home` entries of `layout.yaml`). On the site, tiles
    only read a `KpiView` (`lib/kpiView.ts`) and colours only change through
    tile themes (token overrides, `[data-tile-theme]`): no tile format, prop or
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
    once. **Grain rule:** above the slot filter level only instances of
    day-grain periods (`native_window`) are shown, so every live KPI needs
    a day-grain period (`day`, `sunset` or `overnight`); time-slot instances
    only appear once a slot chip is chosen (`isDayGrain`).
22. **Fallback, never silence.** A KPI that cannot be recomputed keeps the
    rows of its latest run for periods still to come (`read_gold`, original
    `generated_at`), shown as stale. Every unit reports a state; a missing CI
    report counts as `down`. `diamond/status.json` is built once per refresh
    after every massif payload (`bluebird status`).
23. **CI jobs share the run id** chosen by `plan` (`--run-id`); never compute
    dates from each job's own clock. `--run-id` older than 3 h is refused
    with the bronze layer.
24. **Places restrict views, never data.** Zones and linked areas are
    configuration only (`massifs.yaml` `zones`, stations `zone`/`domain`);
    the pipeline still computes and publishes per massif. The site narrows
    each `KpiView` to the chosen stations (`viewFor(…, only)`), so ranks,
    bars and reliability describe the chosen place.

25. **Webcams are links, never images.** Station `webcams` (config) are
    only linked from the LIVE badge of a tile with a `webcam` rule, and only
    while the period shown is in progress (today): a webcam shows the
    present, never a forecast. Never display, download or store a webcam
    image (resort webcams are all rights reserved) until the owner agrees;
    `visual: webcam` is the planned background (README.md "Roadmap").

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
| Add a station | `config/stations/<massif>.yaml` (with `short_name`, `zone`, optional `domain`, optional `webcams`), folder `web/src/assets/photos/<massif>/<id>/.gitkeep` | `bluebird reference --massif <massif>`, `bluebird validate`, `npm test` |
| Add a foreign resort | its zone in `config/massifs.yaml` (`country`: ES, AD…; Spain by comunidad autónoma), the station with checked coordinates | `bluebird reference --massif <massif>`, `bluebird validate`; check the ensemble quota (+2 locations per resort) |
| Add a massif | `config/massifs.yaml` (with its `zones`), new `config/stations/<id>.yaml`, optional `layout.yaml` override | `bluebird reference --massif <id>`, `bluebird validate`, `bluebird demo` |
| Add reference data | `bronze/extractor_<x>.py`, `silver/transformer_<x>.py` with `reference_suffix`, `reference_file`, `read_reference`; source with `schedule: reference` | `bluebird reference`, `pytest`, commit `config/reference/` |
| Add a source | `bronze/extractor_<x>.py` (one grouped request if the API allows), `silver/transformer_<x>.py`, `config/sources.yaml` (+ attribution), tests | `bluebird validate`, `pytest` |
| Add a KPI | `gold/aggregator_<x>.py` (live: `compute(ctx, ref, period)`), PROJECT.md "Available indicators", README.md "Tiles on the site", `config/kpis.yaml` (name, description, `method` with `{param}` placeholders, params, drivers, filters, `periods` for live KPIs, including a day-grain one (`day`, with `day_or_slot` for KPIs that also have slots), `display`: percent / value / levels), `config/tiles.yaml` (live: title with `{period}`), its group in `config/filters.yaml`, `config/layout.yaml`, tests, TILES.md §7 | `bluebird validate`, `pytest`, `bluebird demo` |
| Add a period | `config/periods.yaml` (slot + labels per day; keep slots tiling the day), `periods` of the KPIs | `bluebird validate`, `pytest`, `bluebird demo` |
| Add a tile format | TILES.md (§2, a picture in `docs/tiles/render.mjs`, §7), README.md "Tiles on the site" when used, `web/src/tiles/Tile<Xyz>.svelte`, `web/src/tiles/registry.ts` (id `xyz` + `skeletonVariant` + `tileRows`), `TileFormat` in `config.py`, `config/tiles.yaml` (`format: xyz`) | `bluebird schemas`, `npm run gen:types`, `npm run check`, `npm test`, 390 px screenshots |
| Link a station webcam | TILES.md §5/§7, `webcams` of the station in `config/stations/<massif>.yaml` (`position`, `provider`, official `url`), tile `webcam: { positions, min_probability }` (live `full`/`banner` only) | `bluebird validate`, `npm test`, 390 px screenshot with a frozen clock (the badge only shows while the period is in progress) |
| Change the diamond shape | `diamond/models.py`, displayer, frontend usage | `bluebird schemas`, `npm run gen:types`, `bluebird demo`, all tests |
| Reorder tiles | `config/layout.yaml` (`home` = home page in priority order, `default`/`overrides` = order under a filter), README.md "Tiles on the site", TILES.md §7 (layout order) | `bluebird validate`, `npm test` |
| Add a filter | `config/filters.yaml` (`levels`, `groups`), `filters: [id]` on KPIs in `config/kpis.yaml` | `bluebird validate`, `npm test` |
| Add a kind of filter level | `FilterLevel` in `config.py`, `LEVEL_KINDS` in `web/src/lib/filterLevels.ts`, its `{fr, en, es}` chip labels in config, tests (max 4 levels: `MAX_FILTER_LEVELS`) | `bluebird schemas`, `npm run gen:types`, `pytest`, `npm test` |
| Add a banner photo | found on [Openverse](https://openverse.org/fr) under a reusable licence (CC0, PDM, CC BY, CC BY-SA; never ND), checked on its source page; `web/src/assets/photos/<path>.webp` (≤ 300 KB), `credits.yaml` (author, licence, source URL, changes made), tile `visual: photo` | `npm test`, `npm run build`, 390 px screenshots |
| Add a page | `config/pages.yaml` (`pages[]`, optional `footer.pages`) | `bluebird validate`, `npm test`, 390 px screenshots |
| Add another kind of over-page | content inside `components/Sheet.svelte`, opened with `sheets.open(id)` (`lib/sheets.svelte.ts`) | `npm run check`, `npm test` |
| Add a Rewind | `config/rewinds.yaml`, its filter (`theme: rewind`, no levels) first in `filters.yaml`, KPI tags, tiles of any type + layout (Rewind and theme come from the KPI), TILES.md §7 | after the season: `bluebird rewind --rewind <id>`, review and commit `config/rewind/<id>/` |
| Add a historical KPI | `gold/aggregator_season_<x>.py` (`SeasonAggregator`, value in its native unit), `kpis.yaml` (`kind: historical`, `value {unit, decimals, scale, max}` — snow totals use `m` with `scale: 0.01`, percentages `%` with `scale: 100, max: 100`; method, drivers, filter), PROJECT.md "Available indicators", README.md "Tiles on the site", Rewind `kpis`, tile + layout, tests, TILES.md §7 | `bluebird validate`, `pytest`, `bluebird rewind --no-fetch` |
| Add a UI string | `web/src/lib/i18n/fr.json`, `en.json` **and** `es.json` | `npm test` |
| Add a UI language | `LOCALES`, `LOCALE_NAMES`, `LOCALE_FLAGS` in `web/src/lib/i18n/core.ts` (+ its flag in `Flag.svelte`, `--flag-*` tokens), `<locale>.json`, `INTL_LOCALE` in `lib/format.ts`, the field in `Localized` (`config.py`), the label in every `{…}` object of `config/`, test fixtures (web and the YAML snippets of `pipeline/tests/test_config.py`) | `bluebird validate`, `bluebird schemas`, `npm run gen:types`, `pytest`, `npm test` |
| Change the logo or its colours | `web/src/components/LogoMark.svelte`, lens/frame tokens in `web/src/styles/tokens.css`, phase hours in `web/src/lib/timeOfDay.ts`, the `day` copies `web/public/favicon.svg` and `web/scripts/apple-touch-icon.svg` | `web/scripts/make-apple-icon.sh`, `npm test`, 390 px screenshots |

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
- **Colon in a plain YAML value.** `fr: Vent … créneau : les remontées…`
  is invalid YAML (`: ` starts a mapping); quote such values.
- **YAML flow mappings.** `{ fr: Neige, scénario haut }` splits on the comma.
  Quote such values or use a dash.
- **SVG and CSS variables.** `var()` does not work in SVG presentation
  attributes (`fill="var(--x)"`); use `style="fill: var(--x)"`.
- **SVG gradient ids.** Several inline SVGs on one page share the document's id
  space; a fixed `id="sky"` makes every banner use the first one. Prefix ids
  with `$props.id()` (see `BannerArt.svelte`).
- **Dots on a photo.** On `full` tiles the odds buttons are white glass on a
  dark image: filled dots in `--prob-high` (blue) vanish there. `OddsRow`
  sets `--dot-on: currentColor` and `--dot-off` at 35 % on `.overlay`; any
  mark drawn on an image uses the white text colour (TILES.md §9).
- **Graphics on the odds buttons.** `--track` is almost the colour of
  `--pill-bg`, so empty reliability dots drawn with it vanish on the
  light-blue buttons. `OddsRow` sets `--dot-off` to a mix of `currentColor`
  (and `--dot-on: currentColor` when pressed); do the same for any new mark
  drawn on a pill.
- **`inert` blurs the opener.** App makes the page `inert` in the same update
  that renders a sheet, so `document.activeElement` read in the sheet's
  `$effect` is already `<body>` and focus cannot return to the footer link.
  Capture the opener in `$effect.pre` (see `Sheet.svelte`,
  `ChoicePopup.svelte`; the former side menu had this bug).
- **`element.click()` does not focus.** A DevTools-protocol check of
  "focus returns to the opener" must `focus()` the button before the
  scripted `click()`, as a keyboard user would; otherwise the opener is
  `<body>` and the check fails for the wrong reason.
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
- **Synthetic demo weather needs a day/night cycle.** With a constant
  temperature per member, every thaw/refreeze KPI showed 0 % in the demo;
  `demo.py` adds a daily temperature cycle. Keep it when editing the demo.
- **Windows of the 00:00 refresh.** That run belongs to the previous ski day
  and requests data from the previous UTC date: check that a new KPI's
  lookback still fits `past_days` and its look-ahead `forecast_days`
  (e.g. 48 h before 09:00, 36 h after 06:00 tomorrow).
- **Duplicate YAML keys.** PyYAML keeps the last value of a repeated key, the
  site's YAML plugin refuses it: a KPI inserted in the middle of another
  one's `drivers` passed `bluebird validate` but broke `npm test`. The config
  loader now rejects duplicate keys (`_StrictLoader` in `config.py`).
- **`$props.id()` placement.** It must be the whole initializer of a
  top-level `const` (`const uid = $props.id();`); inside a template literal
  svelte-check reports `props_id_invalid_placement` and the build fails.
- **Logo copies.** The favicon and the home-screen icon are hand-kept copies
  of `LogoMark.svelte` (`day` lens). Change all three together, rerun
  `web/scripts/make-apple-icon.sh`; `brandIcons.test.ts` fails otherwise.
- **Adding a language to `config/`.** About 300 `{fr, en}` objects, most in
  flow style: insert the new key as text next to `en` (a YAML round-trip
  reformats the files and wraps or joins long lines). Two traps met with
  Spanish: automatic wrapping of folded scalars split "Météo-France" at the
  hyphen (shown "Météo- France"; wrap without breaking on hyphens), and
  `pipeline/tests/test_config.py` edits `config/*.yaml` by exact line
  (`{ fr: Non, en: "No" }`…), so its snippets need the new key too. Some
  period labels are shared by two periods but need different words in the
  new language ("demain soir": sunset → "mañana por la tarde", evening slot →
  "mañana por la noche").
- **Variable named `window`** in a component shadows the global object; use
  another name (`timeWindow`).
- **Scrolling a bar whose chips are about to change.** `scrollTo` in the
  click handler runs before Svelte replaces the chips, so the bar ends up
  scrolled after a filter level change. `await tick()` first (see
  `FilterBar.svelte` `choose`).
- **TypeScript is pinned to 6.x.** svelte-check does not support TypeScript 7
  alone yet.
- **Headless Chrome** enforces a ~500 px minimum window width; screenshot the
  site inside a 390 px iframe to check mobile layout.
- **Headless Chrome virtual time** (`--virtual-time-budget`) never completes
  Svelte `out:` transitions: leaving elements stay in the DOM and filters look
  broken. Test transitions in real time by driving Chrome through the DevTools
  protocol (`--remote-debugging-port`, `Runtime.evaluate` from a Node script).
- **Generated files** (`config/schemas`, `web/src/lib/generated`) are checked
  in CI; `docs/tiles/*.svg` come from `node docs/tiles/render.mjs`; regenerate rather than hand-edit. `config/rewind/` is regenerated
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

- **Skaping webcam pages hide the provider.** Resort sites embed the
  Skaping player in an `<iframe>`; a text/markdown fetch of the page shows no
  webcam at all. Read the raw HTML for `skaping.com/<resort>/<cam>/<view>`
  URLs. The player page's `og:image` gives the still JPG pattern
  (`skaping.s3.gra.io.cloud.ovh.net/…/YYYY/MM/DD/large/HH-MM.jpg`, every
  30 min, 403 when missing) for the planned background.
- **No Prettier config in `web/`.** `npx prettier --write` falls back to
  double quotes and rewrites a whole file; it also skips `.svelte` files.
  Keep the existing style (single quotes, 2 spaces) by hand.
- **Tuple types from `min_length` lists.** A pydantic list with
  `min_length=1` becomes a TS tuple (`[T, ...T[]]`) in the generated types:
  a plain `T[]` literal does not type-check in tests; build it with a typed
  helper (see `ruleOf` in `lib/webcams.test.ts`).
- **A tapped button keeps the focus.** After a mouse click or a tap on a
  chip, `document.activeElement` is that chip: a "don't fold while the focus
  is in the bars" guard then blocked folding for good after the first filter
  choice. Guard only keyboard focus (`matches(':focus-visible')`). To test it,
  tap with `Input.dispatchMouseEvent` (DevTools protocol): `element.click()`
  does not focus (see above).
- **Folding header vs scroll position.** Folding the header changes the page
  height; at the bottom of a short page the browser then moves `scrollY` by
  itself, which reads as a scroll up and reopens the bars (a loop).
  `AppHeader` ignores scroll events for 420 ms after each fold, only moving
  the anchor. To test it with the DevTools protocol, scroll by a relative
  amount (`scrollY - 140`): two absolute `scrollTo` past the end of a short
  page clamp to the same position and fire no event; screenshots of a
  scrolled page need `clip.y = scrollY`.
- **An image running under a sibling.** In `TileFull`, the image overflows
  `.hero` down under the "see all" bar of `.below`. `.hero` is positioned
  (`isolation: isolate`), so it paints above the in-flow `.below` and hides
  the button: `.below` needs `position: relative; z-index: 1`. The card body
  (`overflow: hidden`, radius) clips the image at the card's edge.
- **SVG mockups and quotes.** An `aria-label` with unescaped `"` makes the
  whole SVG invalid and GitHub shows a broken image; `render.mjs` escapes
  quotes (`esc`). Check the files with `xmllint --noout docs/tiles/*.svg`.
- **Tile option `photo` is gone.** It is rejected by `bluebird validate`
  (use `visual: photo`); `compact` tiles reject `visual` and `webcam`.

## 9. Definition of done

A change is done when all of these pass locally:

```bash
cd pipeline && uv run ruff format --check . && uv run ruff check . \
  && uv run bluebird validate && uv run bluebird schemas --check && uv run pytest
cd ../web && npm run gen:types && git diff --exit-code -- src/lib/generated \
  && npm run check && npm test && npm run build
```

…and, for UI changes, the page was looked at on a 390 px wide viewport in
light and dark mode, in French, English and Spanish. Update README.md, PROJECT.md and
this file when behaviour, commands or conventions change.

## 10. Roadmap context

The massif bar has place levels (massif → zone → linked area); adding the
Alps or foreign resorts is configuration, but mind the Open-Meteo ensemble
quota (every location weighs) and the payload size of large massifs
(README.md "Future features").
Indicators are grouped into six categories (Snow, Snow quality, Sky,
Comfort, Getting there, Safety; PROJECT.md "Categories" and "Future
indicators"), the level-1 filters today. Every live KPI feasible with the
fetched data is built; the remaining future ones need new data (UV index,
live snow depth, a base band in the ensemble, gusts, avalanche bulletin,
school holidays, nordic sites). Planned filter levels (PROJECT.md "Coming next", README.md
"Future features"): activity (level 1, next to the Rewind) → category →
terrain (piste difficulty from `domain_features`, instead of a skier level)
→ day → time slot, `MAX_FILTER_LEVELS` 5, single-choice levels skipped.
Reference pistes/lifts are used by the Rewind (domain and off-piste
sampling points) but not by any live KPI or tile yet. Future KPIs (live,
Rewind, All Time) are listed in PROJECT.md "Future indicators"; future
features, their feasibility and the planned tile ordering algorithm
(`rankTiles`, `ordering` in `layout.yaml`) in README.md "Future features".
Periods are ready for longer horizons: weekend and week periods (needs
`horizon_days`/period kinds beyond today and tomorrow, and more forecast
days, then a `week` filter level kind).
Animated KPI banners (README.md "Roadmap"): when `visual: photo` finds no
free photo, `BannerArt.svelte` would animate a scene per KPI (falling snow,
sun rays, fog, stars…) in SVG/CSS, inside the banner only (invariant 14:
the page background stays plain), paused off screen and static with
reduced motion; photos stay the first choice (Openverse, CC licences).
Tile axes ready for what comes next: `scope: station` (one resort, its own
values instead of a ranking, for a future station view) and `visual: webcam`
(the leading station's live webcam image as the tile background, today only,
once Skaping or the resort agrees; README.md "Roadmap" has the image URL
pattern and the constraints). Until then only the LIVE link exists.
Planned "Autour de moi" place chip, first of the massif bar (README.md
"Roadmap"): the N nearest stations by road within one hour's drive. Road
times come from drive-time isochrones per station (15/30/45/60 min, winter
passes excluded) precomputed by `bluebird reference` and committed as
reference data; the site tests the browser position against them locally,
never sends or stores it, and narrows views with `viewFor(…, only)`
(invariant 24). No routing API at runtime.
Place stories (full-screen highlights of the day for the chosen place,
README.md "Future features") reuse `viewFor(…, only)` and the planned
`rankTiles`; the current tile design stays (a 2026-11 redesign study kept it).
For the sunniest resort, use the stored `shortwave_wm2`, not `sunshine_s`
(see §8). Planned next (see PROJECT.md): Météo-France avalanche bulletin (BRA, needs an
API key), resort opening status (scraper), slope/aspect from an IGN or
Copernicus elevation model, 7-day trend tile, map tile using
`domain_features`, more massifs (Alps), probability calibration against
observed snow using the gold history.
