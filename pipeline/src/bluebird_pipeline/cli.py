"""Command-line interface: ``bluebird <command>``.

Commands:

- ``validate``  check configuration files, cross-references and plugins.
- ``schemas``   regenerate (or ``--check``) the JSON Schemas in ``config/schemas``.
- ``plugins``   list registered extractors, transformers, aggregators, displayers.
- ``run``       execute pipeline layers on daily data.
- ``reference`` refresh reference files (pistes, lifts…) in ``config/reference``.
- ``rewind``    build the Rewind of a closed season in ``config/rewind``.
- ``demo``      write synthetic demo data to ``web/public/data`` (frontend dev).
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import date
from pathlib import Path

from .checks import plugin_errors
from .config import ConfigError, load_config
from .context import RunContext
from .paths import default_data_dir
from .registry import load_plugins
from .runner import LAYERS, run_pipeline
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
    for rewind in config.rewinds:
        for massif_id in rewind.massifs:
            if not (config.root / "rewind" / rewind.id / f"{massif_id}.json").is_file():
                print(
                    f"warning: config/rewind/{rewind.id}/{massif_id}.json is missing; "
                    f"run `uv run bluebird rewind --rewind {rewind.id}`"
                )
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


def _cmd_run(args: argparse.Namespace) -> int:
    config = load_config(args.config_dir)
    layers = list(LAYERS) if args.layer == "all" else [args.layer]
    sources = config.enabled_sources(schedule="daily", only=args.source or None)
    for schedule, command in (("reference", "reference"), ("season", "rewind")):
        refused = [s.id for s in sources if s.schedule == schedule]
        if refused:
            print(
                f"{', '.join(refused)}: {schedule} source(s); use `bluebird {command}` instead.",
                file=sys.stderr,
            )
            return 2
    storage = LocalStorage(args.data_dir or default_data_dir())
    ctx = RunContext.create(config, storage, run_date=args.date, massif_ids=args.massif or None)
    today = RunContext.create(config, storage, massif_ids=args.massif or None).run_date
    if "bronze" in layers and ctx.run_date != today:
        # Live sources always return the current forecast: storing it under another
        # date would silently corrupt history.
        print(
            f"--date {ctx.run_date} cannot be used with the bronze layer (today is {today}). "
            "Use --layer silver, gold or diamond to recompute a stored day.",
            file=sys.stderr,
        )
        return 2
    report = run_pipeline(ctx, layers, sources)

    print(f"\nRun {ctx.run_id} for {ctx.run_date}: {len(report.written)} file(s) written")
    for message in report.errors:
        print(f"  error: {message}", file=sys.stderr)
    if args.strict and report.errors:
        return 1
    # Without --strict, succeed as long as the last requested layer produced output.
    return 0 if report.wrote_layer(layers[-1]) else 1


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


def _cmd_rewind(args: argparse.Namespace) -> int:
    from .rewind import is_over, run_rewind

    config = load_config(args.config_dir)
    rewinds = [config.rewind(r) for r in args.rewind] if args.rewind else config.rewinds
    rewinds = [r for r in rewinds if r.enabled]
    if not rewinds:
        print("No enabled rewind in config/rewinds.yaml.", file=sys.stderr)
        return 2
    storage = LocalStorage(args.data_dir or default_data_dir())
    status = 0
    for rewind in rewinds:
        massif_ids = [m for m in rewind.massifs if not args.massif or m in args.massif]
        if not massif_ids:
            continue
        ctx = RunContext.create(config, storage, massif_ids=massif_ids, rewind=rewind)
        if not args.no_fetch and not is_over(rewind, ctx.run_date):
            # The archive of an unfinished season is incomplete: never store it.
            print(
                f"rewind {rewind.id}: the season ends on {rewind.end}; "
                "it can be fetched from the next day.",
                file=sys.stderr,
            )
            status = 2
            continue
        report = run_rewind(ctx, fetch=not args.no_fetch, only=args.source or None)
        written = [key for key in report.written if key.startswith("rewind/")]
        print(f"\nRewind {rewind.id} ({ctx.run_id}): {len(written)} file(s) in {config.root}")
        for key in written:
            print(f"  {key}")
        for message in report.errors:
            print(f"  error: {message}", file=sys.stderr)
        if report.errors:
            status = max(status, 1)
    return status


def _cmd_demo(args: argparse.Namespace) -> int:
    from .demo import build_demo
    from .paths import repo_root

    config = load_config(args.config_dir)
    out_dir = args.out or repo_root() / "web" / "public" / "data"
    report = build_demo(config, out_dir)
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

    run = sub.add_parser("run", help="run pipeline layers")
    run.add_argument("--layer", choices=["all", *LAYERS], default="all")
    run.add_argument(
        "--date", type=date.fromisoformat, help="forecast date YYYY-MM-DD (default: today)"
    )
    run.add_argument("--massif", action="append", help="restrict to a massif (repeatable)")
    run.add_argument(
        "--source",
        action="append",
        help="run only this source, including on_demand ones (repeatable)",
    )
    run.add_argument("--data-dir", type=Path, help="storage root (default: <repo>/data)")
    run.add_argument("--strict", action="store_true", help="fail on any error")
    run.set_defaults(func=_cmd_run)

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

    rew = sub.add_parser("rewind", help="build the Rewind of a closed season in config/rewind")
    rew.add_argument("--rewind", action="append", help="rewind id, e.g. 2025-26 (repeatable)")
    rew.add_argument("--massif", action="append", help="restrict to a massif (repeatable)")
    rew.add_argument(
        "--source",
        action="append",
        help="fetch only this season source (repeatable); the others' rows are kept",
    )
    rew.add_argument("--data-dir", type=Path, help="storage root (default: <repo>/data)")
    rew.add_argument(
        "--no-fetch",
        action="store_true",
        help="recompute the KPIs from the committed hourly files, without calling the source",
    )
    rew.set_defaults(func=_cmd_rewind)

    demo = sub.add_parser("demo", help="write synthetic demo data for the frontend")
    demo.add_argument("--out", type=Path, help="default: <repo>/web/public/data")
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
