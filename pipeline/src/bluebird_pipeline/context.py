"""Run context shared by every layer of one pipeline execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import polars as pl

from .config import Config, Massif, Rewind, StationRef
from .storage import Storage, latest_key
from .storage.keys import silver_prefix


def make_run_id(now: datetime) -> str:
    """Sortable run identifier, e.g. ``20261214T053000Z``."""
    return now.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")


@dataclass
class RunContext:
    """Everything a layer needs to know about the current run.

    ``run_date`` is the *forecast date*: the local ski day the KPIs describe.
    """

    config: Config
    storage: Storage
    run_date: date
    run_id: str
    generated_at: datetime
    massif_ids: list[str] | None = None
    #: The season being reviewed, for `bluebird rewind` runs (None for daily runs).
    rewind: Rewind | None = None
    _silver_cache: dict[str, pl.DataFrame | None] = field(default_factory=dict, repr=False)
    _reference_cache: dict[str, pl.DataFrame | None] = field(default_factory=dict, repr=False)

    @classmethod
    def create(
        cls,
        config: Config,
        storage: Storage,
        run_date: date | None = None,
        massif_ids: list[str] | None = None,
        now: datetime | None = None,
        rewind: Rewind | None = None,
    ) -> RunContext:
        now = now or datetime.now(UTC)
        if run_date is None:
            first = config.enabled_massifs(massif_ids)
            tz = first[0].tz if first else ZoneInfo("UTC")
            run_date = now.astimezone(tz).date()
        return cls(
            config=config,
            storage=storage,
            run_date=run_date,
            run_id=make_run_id(now),
            generated_at=now.astimezone(UTC).replace(microsecond=0),
            massif_ids=massif_ids,
            rewind=rewind,
        )

    # -- configuration shortcuts ----------------------------------------------

    def massifs(self) -> list[Massif]:
        return self.config.enabled_massifs(self.massif_ids)

    def stations(self) -> list[StationRef]:
        return self.config.station_refs(self.massif_ids)

    # -- time helpers -----------------------------------------------------------

    def local_datetime(self, massif: Massif, wall_clock: time, day_offset: int = 0) -> datetime:
        """Aware datetime for ``wall_clock`` on ``run_date + day_offset`` in the massif timezone."""
        day = self.run_date + timedelta(days=day_offset)
        return datetime.combine(day, wall_clock, tzinfo=massif.tz)

    # -- silver access ------------------------------------------------------------

    def silver(self, dataset: str) -> pl.DataFrame:
        """Latest silver table of ``dataset`` for ``run_date``; raise if missing."""
        frame = self.silver_optional(dataset)
        if frame is None:
            raise FileNotFoundError(
                f"no silver data for dataset '{dataset}' on {self.run_date}; "
                "run the bronze and silver layers first"
            )
        return frame

    def silver_optional(self, dataset: str) -> pl.DataFrame | None:
        """Latest silver table of ``dataset`` for ``run_date``, or ``None``."""
        if dataset not in self._silver_cache:
            key = latest_key(self.storage, silver_prefix(dataset, self.run_date), ".parquet")
            self._silver_cache[dataset] = self.storage.read_parquet(key) if key else None
        return self._silver_cache[dataset]

    def invalidate_silver(self) -> None:
        self._silver_cache.clear()

    # -- reference access ---------------------------------------------------------

    def reference(self, dataset: str) -> pl.DataFrame | None:
        """Committed reference table of ``dataset`` (e.g. ``domain_features``).

        Unlike :meth:`silver`, this does not depend on ``run_date``: reference
        files live in ``config/reference/`` and are refreshed once a season.
        Rows are limited to the stations of this run. ``None`` if never built.
        """
        if dataset not in self._reference_cache:
            from .reference import load_reference

            self._reference_cache[dataset] = load_reference(self.config, dataset, self.massif_ids)
        return self._reference_cache[dataset]
