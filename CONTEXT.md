# CONTEXT.md — briefing for AI coding assistants

Read this file before changing anything in the repository. It states what
Bluebird is, how the code is organised, the invariants you must keep, and the
exact commands that prove a change works. Human-oriented docs:
[README.md](README.md) (developers) and [PROJECT.md](PROJECT.md) (product).

The mandatory rules for every prompt (documentation updates, languages, Git,
quality bar, end-of-task checklist) are in [AGENTS.md](AGENTS.md). Claude Code
loads both files through `CLAUDE.md`; Codex reads `AGENTS.md` natively.

## 1. What the project is

- A **static website** (Svelte 5 + Vite, mobile first) showing, every morning,
  the probability of good ski conditions in French ski resorts.
- A **Python data pipeline** that fetches weather forecasts, computes the
  probabilities, and writes small JSON files the website reads.
- First massif: Pyrenees, 18 stations. Three KPIs: `snowfall_chance`,
  `onpiste_powder_chance`, `offpiste_powder_chance`.
- The UI mimics a sports-betting page: one tile per KPI, stations ranked by
  descending probability. Style: betting-app look (Betclic-like) in dark
  blue, light blue and white, sober plain background, no background animation.
  Header: logo + title left, menu (massif, language) right, filter bar below.
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
| `config/*.yaml`, `config/stations/*.yaml` | Single source of truth for massifs, stations, KPIs, tiles, layout, sources. Human-edited. |
| `config/reference/<dataset>/<massif>.geojson` | **Fetched** reference data (pistes, lifts) written by `bluebird reference`, committed via PR. Never edit by hand. |
| `config/schemas/*.schema.json` | **Generated** by `uv run bluebird schemas`. Never edit by hand. |
| `pipeline/src/bluebird_pipeline/config.py` | Strict pydantic models for every YAML file + cross-file checks. |
| `pipeline/src/bluebird_pipeline/registry.py` | `Registry` class + `load_plugins()` autodiscovery of the 4 layer packages. |
| `pipeline/src/bluebird_pipeline/context.py` | `RunContext`: config, storage, `run_date` (local forecast date), `run_id`, silver access, local-time helpers. |
| `pipeline/src/bluebird_pipeline/runner.py` | Runs layers in order; isolates failures per source / KPI / displayer; `RunReport`. |
| `pipeline/src/bluebird_pipeline/bronze/` | `base.py` (`Extractor`, `BronzeRecord`, `BronzeBatch`, HTTP retry/throttle) + `extractor_*.py`. |
| `pipeline/src/bluebird_pipeline/silver/` | `base.py` (`Transformer`, `conform`) + `transformer_*.py` + `_open_meteo.py` parser. |
| `pipeline/src/bluebird_pipeline/gold/` | `base.py` (`Aggregator`, `KpiResult`, gold table I/O) + `aggregator_*.py` + `_ensemble.py` helpers. |
| `pipeline/src/bluebird_pipeline/diamond/` | `base.py` (`Displayer`), `models.py` (**frontend contract**), `displayer_*.py`. |
| `pipeline/src/bluebird_pipeline/storage/` | `Storage` ABC, `LocalStorage`, key conventions in `keys.py`. |
| `pipeline/src/bluebird_pipeline/reference.py` | Reference data: `refresh_references()`, `load_reference()`, `missing_references()`. |
| `pipeline/src/bluebird_pipeline/demo.py` | Synthetic weather + `build_demo()` used by `bluebird demo`. |
| `pipeline/tests/` | pytest; `_factories.py` builds Open-Meteo payloads with the real key naming. |
| `web/src/lib/config.ts` | Imports the YAML at build time; `resolveLayout()`. |
| `web/src/lib/data.ts` | Fetches `./data/diamond/<massif>/latest.json`. |
| `web/src/lib/i18n/` | `core.ts` (pure), `i18n.svelte.ts` (reactive store), `fr.json`, `en.json`. |
| `web/src/lib/generated/` | **Generated** TS types (`npm run gen:types`). Never edit by hand. |
| `web/src/tiles/registry.ts` | Tile type id → Svelte component (`xyz` → `TileXyz.svelte`, tested). |
| `web/src/tiles/TileBanner.svelte` | Type `banner`: banner (photo or illustration), top stations as odds buttons, "see all". |
| `web/src/tiles/TileBannerFull.svelte` | Type `banner_full`: photo or illustration fills the card behind title and odds. |
| `web/src/tiles/bannerModel.ts`, `OddsRow.svelte`, `RankingMore.svelte` | Shared by both banner tile types. |
| `web/src/tiles/FlipCard.svelte`, `KpiBack.svelte` | Two-sided card of every tile; front = banner, title, odds (no description); back = one section each for description, time window, method, reliability, update, sources. |
| `web/src/lib/transitions.ts` | `arrive` / `leave` tile transitions and `motion()` (reduced-motion aware). |
| `web/src/lib/photos.ts`, `web/src/assets/photos/` | Banner photos `<massif>/<station_id>/<station_id>_<n>.*` (`photo: leader` draws one at random per page load; also `none` / `<path>`) and `credits.yaml`. |
| `web/src/components/AppMenu.svelte`, `FilterBar.svelte`, `Logo.svelte` | Side menu (blur, scroll lock, inert page), filter bar, logo. |
| `web/src/tiles/TileRanking.svelte` | Type `ranking`: compact list (wrapped in `TileShell`). |
| `web/src/tiles/StationRow.svelte`, `StationDetails.svelte` | Shared station row and details panel. |
| `web/src/components/BannerArt.svelte` | Static SVG banner scenes (`snowfall`, `piste`, `offpiste`, `mountain`). |
| `web/src/lib/ranking.ts` | Pure ranking helpers: `sharedWindow`, `splitTop`, `reliability`. |
| `web/src/styles/` | `tokens.css` (role colour tokens, light/dark), `base.css` (page, `.card` frame), `glass.css` (header only). |
| `web/public/data/diamond/` | Demo data for local dev only, produced by `uv run bluebird demo`. |
| `scripts/ci/publish-gh-pages.sh` | The only way anything is written to `gh-pages` (used by workflows). |
| `scripts/setup-github.sh` | One-time GitHub setup, run by the human owner. |
| `.github/workflows/` | `ci.yml`, `deploy.yml`, `daily.yml`, `reference.yml`, `guard-gh-pages.yml`. |

## 3. Data flow and layers

```
sources ──Extractor──▶ bronze ──Transformer──▶ silver ──Aggregator──▶ gold ──Displayer──▶ diamond ──▶ site
```

| Layer | Class prefix | Folder | Format | Storage key |
|---|---|---|---|---|
| bronze | `Extractor` | `bronze/` | gzip JSON (raw, immutable) | `bronze/{source}/{date}/{run_id}.json.gz` |
| silver | `Transformer` | `silver/` | Parquet, canonical units | `silver/{dataset}/date={date}/{run_id}.parquet` |
| gold | `Aggregator` | `gold/` | Parquet, one row per KPI × station × date | `gold/kpis/date={date}/kpis.parquet` |
| diamond | `Displayer` | `diamond/` | minified JSON | `diamond/{massif}/latest.json`, `.../{date}.json`, `diamond/manifest.json` |

Silver datasets today: `ensemble_hourly` (station, band, model, member, hour),
`forecast_hourly` (same schema, member 0), `domain_features` (OSM pistes/lifts
with `coordinates`).

**Three kinds of data:**

| Kind | Examples | Fetched | Stored | Read with |
|---|---|---|---|---|
| Configuration | positions, elevations, grooming times | never (hand-written) | `config/*.yaml` | `ctx.config`, `ctx.stations()` |
| Reference | pistes, lifts (`domain_features`) | once a season, `bluebird reference` | `config/reference/` (committed, PR-reviewed) | `ctx.reference(dataset)` (any date) |
| Daily | weather (`ensemble_hourly`, `forecast_hourly`) | every morning | by date in storage | `ctx.silver(dataset)` (run date only) |

Production storage: bronze and silver are temporary (7-day workflow
artifact); gold and diamond are committed by CI to `gh-pages/data/`;
reference files are committed to `main` through a pull request.

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
10. **Never fetch live data for a past date.** The CLI refuses `--date` with the
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
    (`--tile-*` tokens in `base.css`); new tile types must too. Every tile is a
    `FlipCard`; interactive content inside a tile must be a real button/link or
    carry `data-no-flip`, otherwise a tap on it flips the card. The `.card`
    frame (striped corners) belongs to each face, never to the static wrapper,
    so it rotates with the card.
17. **KPI method text** uses only `{param}` placeholders that exist in the
    KPI `params` (`bluebird validate` checks it), so the explanation on the
    tile back always matches the maths.

## 5. Git rules for agents

Summary of AGENTS.md §3, which is authoritative.

- `main` is the **only long-lived branch** (and the default branch). There is
  no `dev` branch.
- Work on a **short-lived branch** created from `main` (`feat/<topic>`,
  `fix/<topic>`, `docs/<topic>`). **Never push to `main` or `gh-pages`**; never
  force-push. Rulesets block it anyway.
- Changes reach `main` only through a pull request with the `CI result` check
  green. Merging triggers the deploy. Delete the branch after merge.
- `gh-pages` is written exclusively by `deploy.yml` / `daily.yml` through
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
uv run bluebird run [--layer L] [--massif M] [--source S] [--data-dir D] [--strict]
uv run bluebird reference [--massif M] [--source S] [--no-fetch]   # pistes/lifts → config/reference
uv run bluebird demo                # rebuild web/public/data/diamond (synthetic)
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
| Add a source | `bronze/extractor_<x>.py`, `silver/transformer_<x>.py`, `config/sources.yaml` (+ attribution), tests | `bluebird validate`, `pytest` |
| Add a KPI | `gold/aggregator_<x>.py`, `config/kpis.yaml` (name, description, `method` with `{param}` placeholders, params, drivers, filters), `config/tiles.yaml`, `config/layout.yaml`, tests | `bluebird validate`, `pytest`, `bluebird demo` |
| Add a tile type | `web/src/tiles/Tile<Xyz>.svelte`, `web/src/tiles/registry.ts` (id `xyz`), `config/tiles.yaml` | `npm run check`, `npm test`, 390 px screenshots |
| Change the diamond shape | `diamond/models.py`, displayer, frontend usage | `bluebird schemas`, `npm run gen:types`, `bluebird demo`, all tests |
| Reorder tiles | `config/layout.yaml` | `bluebird validate`, `npm test` |
| Add a filter | `config/filters.yaml`, `filters: [id]` on KPIs in `config/kpis.yaml` | `bluebird validate`, `bluebird schemas`, `npm test` |
| Add a banner photo | `web/src/assets/photos/<path>.webp`, `credits.yaml`, tile `photo` option | `npm run build`, 390 px screenshots |
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
  in CI; regenerate rather than hand-edit.
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

Reference pistes/lifts are collected but not used by any KPI or tile yet.
Planned next (see PROJECT.md): Météo-France avalanche bulletin (BRA, needs an
API key), resort opening status (scraper), slope/aspect from an IGN or
Copernicus elevation model, 7-day trend tile, map tile using
`domain_features`, more massifs (Alps), probability calibration against
observed snow using the gold history.
