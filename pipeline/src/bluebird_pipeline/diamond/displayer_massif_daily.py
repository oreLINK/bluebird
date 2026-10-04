"""One JSON payload per massif and day, with every KPI ranking, plus a manifest.

Outputs (relative to the storage root):

- ``diamond/{massif_id}/latest.json``: what the site loads.
- ``diamond/{massif_id}/{date}.json``: dated archive of the same payload.
- ``diamond/manifest.json``: latest date per massif (merged with the previous one).
"""

from __future__ import annotations

from ..config import Massif
from ..context import RunContext
from ..gold.base import KpiResult, frame_to_results
from ..storage import diamond_key, gold_key
from ._payload import source_payloads, station_payloads
from .base import DiamondArtifact, Displayer, register_displayer
from .models import (
    DiamondKpi,
    DiamondManifest,
    DiamondManifestEntry,
    DiamondMassifDaily,
    DiamondRankingEntry,
)

DIAMOND_ROOT = "diamond/"


@register_displayer("massif_daily")
class DisplayerMassifDaily(Displayer):
    """Rank stations by probability for every enabled KPI of every massif."""

    def display(self, ctx: RunContext) -> list[DiamondArtifact]:
        key = gold_key(ctx.run_date)
        if not ctx.storage.exists(key):
            raise FileNotFoundError(f"no gold data at {key}; run the gold layer first")
        results = frame_to_results(ctx.storage.read_parquet(key))

        artifacts: list[DiamondArtifact] = []
        manifest_entries: dict[str, DiamondManifestEntry] = {}
        for massif in ctx.massifs():
            payload = self._massif_payload(ctx, massif, results)
            if not payload.kpis:
                continue
            latest = diamond_key(massif.id, "latest")
            archive = diamond_key(massif.id, ctx.run_date.isoformat())
            artifacts += [DiamondArtifact(latest, payload), DiamondArtifact(archive, payload)]
            manifest_entries[massif.id] = DiamondManifestEntry(
                forecast_date=ctx.run_date,
                generated_at=ctx.generated_at,
                latest=latest.removeprefix(DIAMOND_ROOT),
                archive=archive.removeprefix(DIAMOND_ROOT),
            )

        if manifest_entries:
            artifacts.append(
                DiamondArtifact(
                    diamond_key(None, "manifest"), self._manifest(ctx, manifest_entries)
                )
            )
        return artifacts

    def _massif_payload(
        self, ctx: RunContext, massif: Massif, results: list[KpiResult]
    ) -> DiamondMassifDaily:
        refs = [ref for ref in ctx.stations() if ref.massif.id == massif.id]
        station_ids = {ref.id for ref in refs}
        kpis: dict[str, DiamondKpi] = {}
        for kpi in ctx.config.enabled_kpis(kind="live"):
            rows = [r for r in results if r.kpi_id == kpi.id and r.station_id in station_ids]
            if not rows:
                continue
            sign = 1 if kpi.order == "asc" else -1
            rows.sort(key=lambda r: (sign * r.probability, r.station_id))
            kpis[kpi.id] = DiamondKpi(
                kpi_id=kpi.id,
                aggregator_version=rows[0].aggregator_version,
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
                    for r in rows
                ],
            )
        return DiamondMassifDaily(
            massif_id=massif.id,
            forecast_date=ctx.run_date,
            generated_at=ctx.generated_at,
            timezone=massif.timezone,
            stations=station_payloads(refs),
            kpis=kpis,
            sources=source_payloads(ctx.config.enabled_sources(schedule="daily")),
        )

    def _manifest(
        self, ctx: RunContext, entries: dict[str, DiamondManifestEntry]
    ) -> DiamondManifest:
        key = diamond_key(None, "manifest")
        previous: dict[str, DiamondManifestEntry] = {}
        if ctx.storage.exists(key):
            try:
                previous = DiamondManifest.model_validate(ctx.storage.read_json(key)).massifs
            except ValueError:
                previous = {}
        return DiamondManifest(generated_at=ctx.generated_at, massifs=previous | entries)
