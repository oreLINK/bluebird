"""Final step of a refresh: ``diamond/status.json``, the manifest and a summary.

The status says, for the site footer, what is fresh, partial, stale or down:

- sources (bronze) and transformations (silver): from the step reports, a
  missing report (job crashed or cancelled) counts as ``down``;
- KPIs: from the gold data itself, per period, so values carried over from an
  earlier run show as ``stale``;
- tiles: from the published massif payloads, i.e. exactly what visitors see.

Runs once per refresh, after every massif payload is written: locally at the
end of ``bluebird run``, in CI as the ``status`` job (``bluebird status``).
"""

from __future__ import annotations

from datetime import datetime

import polars as pl

from ..config import Massif, Tile
from ..context import PeriodInstance, RunContext
from ..gold.base import read_gold
from ..report import SEVERITY, State, StepReport, coverage_state, worst
from ..silver.base import TRANSFORMERS
from ..storage import diamond_key, status_key
from .models import (
    DiamondManifest,
    DiamondManifestEntry,
    DiamondMassifDaily,
    DiamondStatus,
    DiamondStatusItem,
    DiamondStatusKpi,
    DiamondStatusPeriod,
    DiamondStatusTile,
)

DIAMOND_ROOT = "diamond/"


def _period_status(
    ctx: RunContext,
    instance: PeriodInstance,
    *,
    ok: int,
    expected: int,
    updated_at: datetime | None,
) -> DiamondStatusPeriod:
    if ok == 0 or updated_at is None:
        state: State = "down"
    elif updated_at < ctx.generated_at:
        state = "stale"
    else:
        state = coverage_state(ok, expected)
    return DiamondStatusPeriod(
        key=instance.key,
        period_id=instance.period_id,
        ski_day=instance.ski_day,
        start=instance.start,
        end=instance.end,
        state=state,
        ok=ok,
        expected=expected,
        updated_at=updated_at,
    )


def _merge(periods: list[DiamondStatusPeriod]) -> DiamondStatusPeriod:
    """Combine the status of one period across massifs."""
    first = periods[0]
    dates = [p.updated_at for p in periods if p.updated_at is not None]
    return first.model_copy(
        update={
            "state": worst(p.state for p in periods),
            "ok": sum(p.ok for p in periods),
            "expected": sum(p.expected for p in periods),
            "updated_at": min(dates) if dates else None,
        }
    )


def kpi_status(ctx: RunContext, gold: pl.DataFrame) -> list[DiamondStatusKpi]:
    """Per-KPI, per-period state of the gold data visible at the run time."""
    out: list[DiamondStatusKpi] = []
    for kpi in ctx.config.enabled_kpis():
        by_key: dict[str, list[DiamondStatusPeriod]] = {}
        order: list[str] = []
        for massif in ctx.massifs():
            expected = sum(1 for ref in ctx.stations() if ref.massif.id == massif.id)
            for instance in ctx.period_instances(massif, kpi.periods):
                rows = gold.filter(
                    (pl.col("kpi_id") == kpi.id)
                    & (pl.col("massif_id") == massif.id)
                    & (pl.col("period_id") == instance.period_id)
                    & (pl.col("forecast_date") == instance.ski_day)
                )
                status = _period_status(
                    ctx,
                    instance,
                    ok=rows["station_id"].n_unique(),
                    expected=expected,
                    updated_at=rows["generated_at"].min() if not rows.is_empty() else None,  # type: ignore[arg-type]
                )
                if instance.key not in by_key:
                    order.append(instance.key)
                by_key.setdefault(instance.key, []).append(status)
        periods = [_merge(by_key[key]) for key in order]
        out.append(
            DiamondStatusKpi(id=kpi.id, state=worst(p.state for p in periods), periods=periods)
        )
    return out


def _layout_tiles(ctx: RunContext, massif: Massif) -> list[Tile]:
    order = ctx.config.layout.overrides.get(massif.id, ctx.config.layout.default)
    tiles = {t.id: t for t in ctx.config.tiles}
    enabled = {k.id for k in ctx.config.enabled_kpis()}
    return [
        tiles[tile_id]
        for tile_id in order
        if tile_id in tiles and any(k in enabled for k in tiles[tile_id].kpis)
    ]


def read_massif_payload(ctx: RunContext, massif_id: str) -> DiamondMassifDaily | None:
    """The published ``latest.json`` of a massif, or ``None`` if absent or outdated."""
    key = diamond_key(massif_id, "latest")
    if not ctx.storage.exists(key):
        return None
    try:
        return DiamondMassifDaily.model_validate(ctx.storage.read_json(key))
    except ValueError:
        return None  # an older schema version: as good as missing


def tile_status(ctx: RunContext, massif: Massif) -> list[DiamondStatusTile]:
    """State of every tile and period visitors of ``massif`` should see now."""
    payload = read_massif_payload(ctx, massif.id)
    expected = sum(1 for ref in ctx.stations() if ref.massif.id == massif.id)
    enabled = {k.id for k in ctx.config.enabled_kpis()}
    out: list[DiamondStatusTile] = []
    for tile in _layout_tiles(ctx, massif):
        for instance in ctx.period_instances(massif, ctx.config.tile_periods(tile)):
            parts: list[DiamondStatusPeriod] = []
            for kpi_id in (k for k in tile.kpis if k in enabled):
                kpi = payload.kpis.get(kpi_id) if payload else None
                period = (
                    next((p for p in kpi.periods if p.key == instance.key), None) if kpi else None
                )
                parts.append(
                    _period_status(
                        ctx,
                        instance,
                        ok=len(period.ranking) if period else 0,
                        expected=expected,
                        updated_at=period.generated_at if period else None,
                    )
                )
            if parts:
                worst_part = max(parts, key=lambda p: SEVERITY[p.state])
                out.append(DiamondStatusTile(tile_id=tile.id, period=worst_part))
    return out


def build_status(ctx: RunContext, steps: list[StepReport]) -> DiamondStatus:
    """Assemble the status of the refresh ``ctx.run_id`` from reports and stored data."""
    reports = {(s.layer, s.id): s for s in steps}
    sources = ctx.config.enabled_sources(schedule="daily")

    def item(layer: str, source_id: str, dataset: str | None = None) -> DiamondStatusItem:
        step = reports.get((layer, source_id))  # type: ignore[arg-type]
        return DiamondStatusItem(
            id=source_id,
            dataset=dataset,
            state=step.state if step else "down",
            ok=step.ok if step else None,
            expected=step.expected if step else None,
        )

    bronze = [item("bronze", s.id) for s in sources]
    silver = [
        item("silver", s.id, getattr(TRANSFORMERS.get(s.transformer), "dataset", None))
        for s in sources
    ]
    kpis = kpi_status(ctx, read_gold(ctx, [k.id for k in ctx.config.enabled_kpis()]))
    tiles = {massif.id: tile_status(ctx, massif) for massif in ctx.massifs()}
    states = [
        *(i.state for i in bronze),
        *(i.state for i in silver),
        *(k.state for k in kpis),
        *(t.period.state for ts in tiles.values() for t in ts),
    ]
    return DiamondStatus(
        generated_at=ctx.generated_at,
        run_id=ctx.run_id,
        ski_day=ctx.run_date,
        state=worst(states, default="ok"),
        sources=bronze,
        transforms=silver,
        kpis=kpis,
        tiles=tiles,
    )


def build_manifest(ctx: RunContext) -> DiamondManifest | None:
    """Latest payload of every massif present in storage (new or previously published)."""
    entries: dict[str, DiamondManifestEntry] = {}
    for massif in ctx.config.enabled_massifs():
        payload = read_massif_payload(ctx, massif.id)
        if payload is None:
            continue
        latest = diamond_key(massif.id, "latest")
        archive = diamond_key(massif.id, payload.forecast_date.isoformat())
        entries[massif.id] = DiamondManifestEntry(
            forecast_date=payload.forecast_date,
            generated_at=payload.generated_at,
            latest=latest.removeprefix(DIAMOND_ROOT),
            archive=archive.removeprefix(DIAMOND_ROOT),
        )
    if not entries:
        return None
    return DiamondManifest(generated_at=ctx.generated_at, massifs=entries)


def summary_markdown(status: DiamondStatus, steps: list[StepReport]) -> str:
    """Human summary of a refresh for the GitHub job page (with error messages)."""
    icon = {"ok": "✅", "partial": "🟡", "stale": "🟠", "down": "🔴"}
    lines = [
        f"## Bluebird refresh `{status.run_id}`",
        "",
        f"Ski day **{status.ski_day}**, overall {icon[status.state]} **{status.state}**.",
        "",
        "| Layer | Unit | State | Stations | Message |",
        "|---|---|---|---|---|",
    ]
    for step in steps:
        stations = f"{step.ok}/{step.expected}" if step.expected is not None else ""
        message = (step.message or "").replace("|", "\\|").replace("\n", " ")
        lines.append(
            f"| {step.layer} | {step.id} | {icon[step.state]} {step.state} | {stations} "
            f"| {message} |"
        )
    reported = {(s.layer, s.id) for s in steps}
    for kind, layer, items in (
        ("source", "bronze", status.sources),
        ("transformation", "silver", status.transforms),
    ):
        for missing in (i for i in items if (layer, i.id) not in reported):
            lines.append(f"| {layer} | {missing.id} | 🔴 down | | no report: {kind} job failed |")
    lines += ["", "| KPI | Period | State | Stations | Values from |", "|---|---|---|---|---|"]
    for kpi in status.kpis:
        for period in kpi.periods:
            updated = period.updated_at.isoformat() if period.updated_at else ""
            lines.append(
                f"| {kpi.id} | {period.key} | {icon[period.state]} {period.state} "
                f"| {period.ok}/{period.expected} | {updated} |"
            )
    return "\n".join(lines) + "\n"


def finalize_refresh(ctx: RunContext, steps: list[StepReport]) -> tuple[DiamondStatus, list[str]]:
    """Write ``status.json`` and ``manifest.json``; return the status and keys written."""
    written: list[str] = []
    manifest = build_manifest(ctx)
    if manifest is not None:
        key = diamond_key(None, "manifest")
        ctx.storage.write_json(key, manifest.model_dump(mode="json"))
        written.append(key)
    status = build_status(ctx, steps)
    ctx.storage.write_json(status_key(), status.model_dump(mode="json"))
    written.append(status_key())
    return status, written
