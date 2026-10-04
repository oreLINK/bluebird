"""Command-line interface: ``bluebird <command>``.

Commands:

- ``validate``  check configuration files, cross-references and plugins.
- ``schemas``   regenerate (or ``--check``) the JSON Schemas in ``config/schemas``.
- ``plugins``   list registered extractors, transformers, aggregators, displayers.
- ``plan``      print the units of a refresh (sources, datasets, KPIs, massifs).
- ``run``       execute pipeline layers on daily data.
- ``status``    write ``diamond/status.json`` and the manifest from step reports.
- ``reference`` refresh reference files (pistes, lifts…) in ``config/reference``.
- ``demo``      write synthetic demo data to ``web/public/data`` (frontend dev).

The CI workflow (``.github/workflows/refresh.yml``) runs ``plan`` once, then one
``run`` per source, dataset, KPI and massif, all with the same ``--run-id``,
then ``status``.
"""

from __future__ import annotations

import argparse
import json
import logging
import shutil
import sys
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from .checks import plugin_errors
from .config import ConfigError, load_config
from .context import RunContext, parse_run_id
from .paths import default_data_dir
from .registry import load_plugins
from .report import read_reports
from .runner import LAYERS, RunReport, finalize, run_pipeline
from .schemas import stale_schemas, write_schemas
from .storage import LocalStorage


def _cmd_validate(args: argparse.Namespace) -> int:
    config = load_config(args.config_dir)
    errors = plugin_errors(config)
    if errors:
        print("Plugin errors:\n  - " + "\n  - ".join(errors), file=sys.stderr)
        return 1
    stations = config.station_refs()
    print(
        f"OK: {len(config.massifs)} massif(s), {len(stations)} station(s), "
        f"{len(config.kpis)} KPI(s), {len(config.tiles)} tile(s), {len(config.sources)} source(s)"
    )
    from .reference import missing_references

    for key in missing_references(config):
        print(f"warning: config/{key} is missing; run `uv run bluebird reference`")
    return 0


def _cmd_schemas(args: argparse.Namespace) -> int:
    config = load_config(args.config_dir)
    directory = config.root / "schemas"
    if args.check:
        stale = stale_schemas(directory)
        if stale:
            print(
                f"Stale schemas: {', '.join(stale)}. Run `uv run bluebird schemas`.",
                file=sys.stderr,
            )
            return 1
        print("Schemas are up to date.")
        return 0
    for path in write_schemas(directory):
        print(f"wrote {path}")
    return 0


def _cmd_plugins(_: argparse.Namespace) -> int:
    from .bronze.base import EXTRACTORS
    from .diamond.base import DISPLAYERS
    from .gold.base import AGGREGATORS
    from .silver.base import TRANSFORMERS

    load_plugins()
    for title, registry in (
        ("bronze extractors", EXTRACTORS),
        ("silver transformers", TRANSFORMERS),
        ("gold aggregators", AGGREGATORS),
        ("diamond displayers", DISPLAYERS),
    ):
        print(f"{title}:")
        for plugin_id, cls in registry.items():
            print(f"  {plugin_id:<28} {cls.__module__}.{cls.__qualname__}")
    return 0


# A live fetch stored under a run id older than this would corrupt history.
MAX_RUN_ID_AGE = timedelta(hours=3)


def _cmd_plan(args: argparse.Namespace) -> int:
    from .silver.base import TRANSFORMERS

    config = load_config(args.config_dir)
    load_plugins()
    storage = LocalStorage(args.data_dir or default_data_dir())
    ctx = RunContext.create(config, storage, run_id=args.run_id)
    sources = config.enabled_sources(schedule="daily")
    plan = {
        "run_id": ctx.run_id,
        "ski_day": ctx.run_date.isoformat(),
        "sources": [s.id for s in sources],
        "silver": [
            {"source": s.id, "dataset": TRANSFORMERS.get(s.transformer).dataset} for s in sources
        ],
        "kpis": [k.id for k in config.enabled_kpis()],
        "massifs": [m.id for m in ctx.massifs()],
    }
    if args.json:
        print(json.dumps(plan, separators=(",", ":")))
    else:
        for name, value in plan.items():
            print(f"{name}: {value}")
    return 0


def _export(report: RunReport, data_dir: Path, target: Path) -> None:
    """Copy the files a run wrote to ``target``, keeping their storage keys as paths."""
    for key in report.written:
        source = data_dir / key
        if source.is_file():
            (target / key).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target / key)


def _write_report(report: RunReport, ctx: RunContext, path: Path | None) -> None:
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(report.to_file(ctx).model_dump_json(indent=2), encoding="utf-8")


def _cmd_run(args: argparse.Namespace) -> int:
    config = load_config(args.config_dir)
    layers = list(LAYERS) if args.layer == "all" else [args.layer]
    sources = config.enabled_sources(schedule="daily", only=args.source or None)
    reference = [s.id for s in sources if s.schedule == "reference"]
    if reference:
        print(
            f"{', '.join(reference)}: reference source(s); use `bluebird reference` instead.",
            file=sys.stderr,
        )
        return 2
    unknown_kpis = set(args.kpi or []) - {k.id for k in config.kpis}
    if unknown_kpis:
        print(f"unknown KPI(s): {', '.join(sorted(unknown_kpis))}", file=sys.stderr)
        return 2
    data_dir = args.data_dir or default_data_dir()
    storage = LocalStorage(data_dir)
    massifs = args.massif or None
    ctx = RunContext.create(
        config, storage, run_date=args.date, massif_ids=massifs, run_id=args.run_id
    )
    if "bronze" in layers:
        # Live sources always return the current forecast: storing it under another
        # date or an old run id would silently corrupt history.
        today = RunContext.create(config, storage, massif_ids=massifs).run_date
        if ctx.run_date != today:
            print(
                f"--date {ctx.run_date} cannot be used with the bronze layer "
                f"(today's ski day is {today}). "
                "Use --layer silver, gold or diamond to recompute a stored day.",
                file=sys.stderr,
            )
            return 2
        if args.run_id and datetime.now(UTC) - parse_run_id(args.run_id) > MAX_RUN_ID_AGE:
            print(f"--run-id {args.run_id} is too old to fetch live data.", file=sys.stderr)
            return 2
    report = run_pipeline(
        ctx,
        layers,
        sources,
        kpi_ids=args.kpi or None,
        final=args.layer == "all" and not args.kpi,
    )
    _write_report(report, ctx, args.report)
    if args.export:
        _export(report, data_dir, args.export)

    print(f"\nRun {ctx.run_id} for ski day {ctx.run_date}: {len(report.written)} file(s) written")
    for message in report.errors:
        print(f"  error: {message}", file=sys.stderr)
    if args.strict and report.errors:
        return 1
    # Without --strict, succeed as long as the last requested layer produced output.
    return 0 if report.wrote_layer(layers[-1]) else 1


def _cmd_status(args: argparse.Namespace) -> int:
    from .diamond._status import summary_markdown

    config = load_config(args.config_dir)
    load_plugins()
    data_dir = args.data_dir or default_data_dir()
    ctx = RunContext.create(config, LocalStorage(data_dir), run_id=args.run_id)
    steps = read_reports(args.reports) if args.reports else []
    report = RunReport()
    finalize(ctx, report, steps)
    if report.errors:
        for message in report.errors:
            print(f"  error: {message}", file=sys.stderr)
        return 1
    from .diamond.models import DiamondStatus
    from .storage import status_key

    status = DiamondStatus.model_validate(ctx.storage.read_json(status_key()))
    if args.summary:
        with args.summary.open("a", encoding="utf-8") as handle:
            handle.write(summary_markdown(status, steps))
    if args.export:
        _export(report, data_dir, args.export)
    print(f"Status of {ctx.run_id}: {status.state}")
    return 0


def _cmd_reference(args: argparse.Namespace) -> int:
    from .reference import refresh_references

    config = load_config(args.config_dir)
    sources = config.enabled_sources(schedule="reference", only=args.source or None)
    not_reference = [s.id for s in sources if s.schedule != "reference"]
    if not_reference:
        print(f"{', '.join(not_reference)}: not reference source(s).", file=sys.stderr)
        return 2
    if not sources:
        print("No enabled reference source.", file=sys.stderr)
        return 2
    storage = LocalStorage(args.data_dir or default_data_dir())
    ctx = RunContext.create(config, storage, massif_ids=args.massif or None)
    report = refresh_references(ctx, sources, fetch=not args.no_fetch)

    written = [key for key in report.written if key.startswith("reference/")]
    print(f"\nReference refresh {ctx.run_id}: {len(written)} file(s) written in {config.root}")
    for key in written:
        print(f"  {key}")
    for message in report.errors:
        print(f"  error: {message}", file=sys.stderr)
    return 1 if report.errors else 0


def _cmd_demo(args: argparse.Namespace) -> int:
    from .demo import build_demo
    from .paths import repo_root

    config = load_config(args.config_dir)
    out_dir = args.out or repo_root() / "web" / "public" / "data"
    report = build_demo(config, out_dir, **({"now": args.now} if args.now else {}))
    for message in report.errors:
        print(f"  error: {message}", file=sys.stderr)
    print(f"Demo data written to {out_dir / 'diamond'}")
    return 1 if report.errors else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bluebird", description=__doc__.splitlines()[0])
    parser.add_argument("--config-dir", type=Path, help="defaults to <repo>/config")
    parser.add_argument("-v", "--verbose", action="store_true", help="debug logging")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("validate", help="validate configuration and plugins").set_defaults(
        func=_cmd_validate
    )

    schemas = sub.add_parser("schemas", help="write JSON Schemas to config/schemas")
    schemas.add_argument("--check", action="store_true", help="fail if schemas are stale")
    schemas.set_defaults(func=_cmd_schemas)

    sub.add_parser("plugins", help="list registered plugins").set_defaults(func=_cmd_plugins)

    plan = sub.add_parser("plan", help="print the units of a refresh")
    plan.add_argument("--json", action="store_true", help="one-line JSON (for CI matrices)")
    plan.add_argument("--run-id", help="pin the run start (default: now)")
    plan.add_argument("--data-dir", type=Path, help="storage root (default: <repo>/data)")
    plan.set_defaults(func=_cmd_plan)

    run = sub.add_parser("run", help="run pipeline layers")
    run.add_argument("--layer", choices=["all", *LAYERS], default="all")
    run.add_argument(
        "--date",
        type=date.fromisoformat,
        help="ski day YYYY-MM-DD (default: the current one, which starts at 06:00)",
    )
    run.add_argument(
        "--run-id", help="pin the run start, e.g. 20261214T050700Z (shared by CI jobs)"
    )
    run.add_argument("--massif", action="append", help="restrict to a massif (repeatable)")
    run.add_argument("--kpi", action="append", help="gold: only this KPI (repeatable)")
    run.add_argument("--report", type=Path, help="write the step report to this JSON file")
    run.add_argument(
        "--export", type=Path, help="copy the files written to this folder (CI artifacts)"
    )
    run.add_argument(
        "--source",
        action="append",
        help="run only this source, including on_demand ones (repeatable)",
    )
    run.add_argument("--data-dir", type=Path, help="storage root (default: <repo>/data)")
    run.add_argument("--strict", action="store_true", help="fail on any error")
    run.set_defaults(func=_cmd_run)

    status = sub.add_parser("status", help="write diamond/status.json and the manifest")
    status.add_argument("--run-id", help="the refresh to describe (default: now)")
    status.add_argument("--reports", type=Path, help="folder of `run --report` JSON files")
    status.add_argument("--data-dir", type=Path, help="storage root (default: <repo>/data)")
    status.add_argument("--summary", type=Path, help="append a Markdown summary to this file")
    status.add_argument("--export", type=Path, help="copy the files written to this folder")
    status.set_defaults(func=_cmd_status)

    ref = sub.add_parser("reference", help="refresh reference files in config/reference")
    ref.add_argument("--source", action="append", help="reference source id (repeatable)")
    ref.add_argument("--massif", action="append", help="restrict to a massif (repeatable)")
    ref.add_argument("--data-dir", type=Path, help="storage root (default: <repo>/data)")
    ref.add_argument(
        "--no-fetch",
        action="store_true",
        help="rebuild from the latest stored bronze batch instead of calling the source",
    )
    ref.set_defaults(func=_cmd_reference)

    demo = sub.add_parser("demo", help="write synthetic demo data for the frontend")
    demo.add_argument("--out", type=Path, help="default: <repo>/web/public/data")
    demo.add_argument(
        "--now",
        type=datetime.fromisoformat,
        help="refresh time to simulate, e.g. 2027-01-15T17:07+00:00 (default: 06:00 refresh)",
    )
    demo.set_defaults(func=_cmd_demo)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    try:
        return args.func(args)
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
