"""One JSON payload per massif with every KPI ranking, per period.

Outputs (relative to the storage root):

- ``diamond/{massif_id}/latest.json``: what the site loads.
- ``diamond/{massif_id}/{ski_day}.json``: dated archive of the same payload.

Only periods not over at the run time are published, and each period keeps the
time its values were computed: values carried over from an earlier run (see
``gold.base.read_gold``) are older than the payload, which the site flags.
``diamond/manifest.json`` is written by the final status step
(:mod:`._status`), once every massif is done.
"""

from __future__ import annotations

import polars as pl

from ..config import Massif
from ..context import RunContext
from ..gold.base import frame_to_results, read_gold
from ..storage import diamond_key
from .base import DiamondArtifact, Displayer, register_displayer
from .models import (
    DiamondElevation,
    DiamondKpi,
    DiamondKpiPeriod,
    DiamondMassifDaily,
    DiamondRankingEntry,
    DiamondSource,
    DiamondStation,
)


@register_displayer("massif_daily")
class DisplayerMassifDaily(Displayer):
    """Rank stations by probability for every KPI and period of every massif."""

    def display(self, ctx: RunContext) -> list[DiamondArtifact]:
        gold = read_gold(ctx, [kpi.id for kpi in ctx.config.enabled_kpis()])
        if gold.is_empty():
            raise FileNotFoundError(
                f"no gold data for {ctx.run_date} or the day before; run the gold layer first"
            )
        artifacts: list[DiamondArtifact] = []
        for massif in ctx.massifs():
            payload = self._massif_payload(ctx, massif, gold)
            if not payload.kpis:
                continue
            artifacts += [
                DiamondArtifact(diamond_key(massif.id, "latest"), payload),
                DiamondArtifact(diamond_key(massif.id, ctx.run_date.isoformat()), payload),
            ]
        return artifacts

    def _kpi_periods(
        self, ctx: RunContext, massif: Massif, kpi_id: str, periods: list[str], gold: pl.DataFrame
    ) -> list[DiamondKpiPeriod]:
        rows = gold.filter((pl.col("kpi_id") == kpi_id) & (pl.col("massif_id") == massif.id))
        out: list[DiamondKpiPeriod] = []
        for instance in ctx.period_instances(massif, periods):
            selected = rows.filter(
                (pl.col("period_id") == instance.period_id)
                & (pl.col("forecast_date") == instance.ski_day)
            )
            if selected.is_empty():
                continue
            results = sorted(
                frame_to_results(selected), key=lambda r: (-r.probability, r.station_id)
            )
            out.append(
                DiamondKpiPeriod(
                    key=instance.key,
                    period_id=instance.period_id,
                    ski_day=instance.ski_day,
                    start=instance.start,
                    end=instance.end,
                    generated_at=selected["generated_at"].max(),  # type: ignore[arg-type]
                    ranking=[
                        DiamondRankingEntry(
                            station_id=r.station_id,
                            probability=r.probability,
                            confidence=r.confidence,
                            window_start=r.window_start.astimezone(massif.tz),
                            window_end=r.window_end.astimezone(massif.tz),
                            members=r.members,
                            drivers=r.drivers,
                        )
                        for r in results
                    ],
                )
            )
        return out

    def _massif_payload(
        self, ctx: RunContext, massif: Massif, gold: pl.DataFrame
    ) -> DiamondMassifDaily:
        refs = [ref for ref in ctx.stations() if ref.massif.id == massif.id]
        kpis: dict[str, DiamondKpi] = {}
        for kpi in ctx.config.enabled_kpis():
            periods = self._kpi_periods(ctx, massif, kpi.id, kpi.periods, gold)
            if not periods:
                continue
            versions = gold.filter(pl.col("kpi_id") == kpi.id)["aggregator_version"]
            kpis[kpi.id] = DiamondKpi(
                kpi_id=kpi.id,
                aggregator_version=str(versions.max()),
                periods=periods,
            )
        return DiamondMassifDaily(
            massif_id=massif.id,
            forecast_date=ctx.run_date,
            generated_at=ctx.generated_at,
            timezone=massif.timezone,
            stations={
                ref.id: DiamondStation(
                    id=ref.id,
                    name=ref.station.name,
                    short_name=ref.station.short_name or ref.station.name,
                    lat=ref.station.lat,
                    lon=ref.station.lon,
                    elevation=DiamondElevation(
                        base=ref.station.elevation.at("base"),
                        mid=ref.station.elevation.at("mid"),
                        summit=ref.station.elevation.at("summit"),
                    ),
                    aspects=list(ref.station.aspects),
                    website=ref.station.website,
                )
                for ref in refs
            },
            kpis=kpis,
            sources=[
                DiamondSource(
                    id=source.id,
                    name=source.attribution.name,
                    url=source.attribution.url,
                    license=source.attribution.license,
                )
                for source in ctx.config.enabled_sources(schedule="daily")
            ],
        )
