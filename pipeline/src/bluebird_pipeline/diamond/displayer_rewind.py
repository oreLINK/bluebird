"""One Rewind payload per massif: every historical KPI of a closed season, ranked.

Output: ``rewind/{rewind_id}/{massif_id}.json``, written by ``bluebird rewind``
into the configuration folder and committed (the site bundles it at build
time). ``schedule = "season"``: never run by the daily pipeline.
"""

from __future__ import annotations

from typing import ClassVar, Literal

from ..context import RunContext
from ..gold.base import frame_to_season_results
from ..storage import rewind_gold_key, rewind_key
from ._payload import source_payloads, station_payloads
from .base import DiamondArtifact, Displayer, register_displayer
from .models import DiamondRewind, DiamondRewindEntry, DiamondRewindKpi

PAYLOAD_SUFFIX = ".json"


@register_displayer("rewind")
class DisplayerRewind(Displayer):
    """Rank stations by value for every KPI of the run's Rewind (KPI `order`, default desc)."""

    schedule: ClassVar[Literal["daily", "season"]] = "season"

    def display(self, ctx: RunContext) -> list[DiamondArtifact]:
        rewind = ctx.rewind
        if rewind is None:
            raise ValueError("the rewind displayer only runs from `bluebird rewind`")
        key = rewind_gold_key(rewind.id)
        if not ctx.storage.exists(key):
            raise FileNotFoundError(f"no gold data at {key}; compute the historical KPIs first")
        results = frame_to_season_results(ctx.storage.read_parquet(key))
        sources = [
            s for s in ctx.config.sources if s.enabled and s.schedule in ("season", "reference")
        ]

        artifacts: list[DiamondArtifact] = []
        for massif in ctx.massifs():
            if massif.id not in rewind.massifs:
                continue
            refs = [ref for ref in ctx.stations() if ref.massif.id == massif.id]
            station_ids = {ref.id for ref in refs}
            kpis: dict[str, DiamondRewindKpi] = {}
            orders = {k.id: k.order for k in ctx.config.kpis}
            for kpi_id in rewind.kpis:
                rows = [r for r in results if r.kpi_id == kpi_id and r.station_id in station_ids]
                if not rows:
                    continue
                sign = 1 if orders.get(kpi_id) == "asc" else -1
                rows.sort(key=lambda r: (sign * r.value, r.station_id))
                kpis[kpi_id] = DiamondRewindKpi(
                    kpi_id=kpi_id,
                    aggregator_version=rows[0].aggregator_version,
                    unit=rows[0].unit,
                    ranking=[
                        DiamondRewindEntry(
                            station_id=r.station_id, value=r.value, drivers=r.drivers
                        )
                        for r in rows
                    ],
                )
            if not kpis:
                continue
            payload = DiamondRewind(
                rewind_id=rewind.id,
                massif_id=massif.id,
                start=rewind.start,
                end=rewind.end,
                generated_at=ctx.generated_at,
                timezone=massif.timezone,
                stations=station_payloads(refs),
                kpis=kpis,
                sources=source_payloads(sources),
            )
            artifacts.append(
                DiamondArtifact(rewind_key(rewind.id, massif.id, PAYLOAD_SUFFIX), payload)
            )
        return artifacts
