# CONTEXT.md — briefing for AI coding assistants

Read this file before changing anything in the repository. It states what
Bluebird is, how the code is organised, the invariants you must keep, and the
exact commands that prove a change works. Human-oriented docs:
[README.md](README.md) (developers) and [PROJECT.md](PROJECT.md) (product).

## 1. What the project is

- A **static website** (Svelte 5 + Vite, mobile first) showing, every morning,
  the probability of good ski conditions in French ski resorts.
- A **Python data pipeline** that fetches weather forecasts, computes the
  probabilities, and writes small JSON files the website reads.
- First massif: Pyrenees, 18 stations. Three KPIs: `snowfall_chance`,
  `onpiste_powder_chance`, `offpiste_powder_chance`.
- The UI mimics a sports-betting page: one tile per KPI, stations ranked by
  descending probability. Style: frosted "Liquid Glass" with a winter theme.
- UI languages: French (default) and English. **All code, comments, docs and
  commit messages are in English.** User-facing strings are in both languages.
- Hosting and storage: **GitHub only** (Pages + the `gh-pages` branch). No
  server, no database, no cloud bucket.

## 2. Repository map

| Path | Role |
|---|---|
| `config/*.yaml`, `config/stations/*.yaml` | Single source of truth for massifs, stations, KPIs, tiles, layout, sources. Human-edited. |
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
| `pipeline/src/bluebird_pipeline/demo.py` | Synthetic weather + `build_demo()` used by `bluebird demo`. |
| `pipeline/tests/` | pytest; `_factories.py` builds Open-Meteo payloads with the real key naming. |
| `web/src/lib/config.ts` | Imports the YAML at build time; `resolveLayout()`. |
| `web/src/lib/data.ts` | Fetches `./data/diamond/<massif>/latest.json`. |
| `web/src/lib/i18n/` | `core.ts` (pure), `i18n.svelte.ts` (reactive store), `fr.json`, `en.json`. |
| `web/src/lib/generated/` | **Generated** TS types (`npm run gen:types`). Never edit by hand. |
| `web/src/tiles/registry.ts` | Tile type id → Svelte component. |
| `web/src/styles/` | `tokens.css` (theme tokens, light/dark), `glass.css`, `base.css`. |
| `web/public/data/diamond/` | Demo data for local dev only, produced by `uv run bluebird demo`. |
| `scripts/ci/publish-gh-pages.sh` | The only way anything is written to `gh-pages` (used by workflows). |
| `scripts/setup-github.sh` | One-time GitHub setup, run by the human owner. |
| `.github/workflows/` | `ci.yml`, `deploy.yml`, `daily.yml`, `guard-gh-pages.yml`. |

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
`forecast_hourly` (same schema, member 0), `domain_features` (OSM pistes/lifts).

Production storage: bronze and silver are temporary (7-day workflow
artifact); gold and diamond are committed by CI to `gh-pages/data/`.

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
    handling, ≥ 4.5:1 text contrast (see `--prob-*` tokens), real `<button>`s
    with `aria-*` state.

## 5. Git rules for agents

- Work on **`dev`** (or a feature branch merged into `dev`). **Never push to
  `main` or `gh-pages`**; never force-push. Rulesets block it anyway.
- Changes reach `main` only through a pull request `dev → main` with the
  `CI result` check green. Merging triggers the deploy.
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
| Add a station | `config/stations/<massif>.yaml` | `bluebird validate` |
| Add a massif | `config/massifs.yaml`, new `config/stations/<id>.yaml`, optional `layout.yaml` override | `bluebird validate`, `bluebird demo` |
| Add a source | `bronze/extractor_<x>.py`, `silver/transformer_<x>.py`, `config/sources.yaml` (+ attribution), tests | `bluebird validate`, `pytest` |
| Add a KPI | `gold/aggregator_<x>.py`, `config/kpis.yaml` (name, description, params, drivers), `config/tiles.yaml`, `config/layout.yaml`, tests | `bluebird validate`, `pytest`, `bluebird demo` |
| Add a tile type | `web/src/tiles/<X>Tile.svelte`, `web/src/tiles/registry.ts`, `config/tiles.yaml` | `npm run check`, `npm test` |
| Change the diamond shape | `diamond/models.py`, displayer, frontend usage | `bluebird schemas`, `npm run gen:types`, `bluebird demo`, all tests |
| Reorder tiles | `config/layout.yaml` | `bluebird validate`, `npm test` |
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
- **Overpass** (OSM) is slow and returns 429/504 often: `on_demand` only.
- **YAML flow mappings.** `{ fr: Neige, scénario haut }` splits on the comma.
  Quote such values or use a dash.
- **SVG and CSS variables.** `var()` does not work in SVG presentation
  attributes (`fill="var(--x)"`); use `style="fill: var(--x)"`.
- **TypeScript is pinned to 6.x.** svelte-check does not support TypeScript 7
  alone yet.
- **Headless Chrome** enforces a ~500 px minimum window width; screenshot the
  site inside a 390 px iframe to check mobile layout.
- **Generated files** (`config/schemas`, `web/src/lib/generated`) are checked
  in CI; regenerate rather than hand-edit.

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

Planned next (see PROJECT.md): Météo-France avalanche bulletin (BRA, needs an
API key), resort opening status (scraper), slope/aspect from an IGN or
Copernicus elevation model, 7-day trend tile, map tile using
`domain_features`, more massifs (Alps), probability calibration against
observed snow using the gold history.
