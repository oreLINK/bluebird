"""Run context shared by every layer of one pipeline execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import polars as pl

from .config import Config, Massif, Period, StationRef, parse_local_time
from .storage import Storage, latest_key
from .storage.keys import silver_prefix

RUN_ID_FORMAT = "%Y%m%dT%H%M%SZ"


def make_run_id(now: datetime) -> str:
    """Sortable run identifier, e.g. ``20261214T053000Z``."""
    return now.astimezone(UTC).strftime(RUN_ID_FORMAT)


def parse_run_id(run_id: str) -> datetime:
    """Inverse of :func:`make_run_id`: the UTC instant a run started."""
    try:
        return datetime.strptime(run_id, RUN_ID_FORMAT).replace(tzinfo=UTC)
    except ValueError as exc:
        raise ValueError(f"invalid run id '{run_id}', expected e.g. 20261214T053000Z") from exc


def ski_day(config: Config, now: datetime, tz: ZoneInfo) -> date:
    """The ski day running at ``now``: the local date, minus one before ``day_start``."""
    local = now.astimezone(tz)
    start = parse_local_time(config.periods.day_start)
    return local.date() - timedelta(days=1) if local.time() < start else local.date()


def _wall_clock(day: date, minutes: int, tz: ZoneInfo) -> datetime:
    """Aware local datetime ``minutes`` after midnight of ``day`` (may roll over)."""
    moment = datetime.combine(day + timedelta(days=minutes // 1440), time(0), tzinfo=tz)
    minute = minutes % 1440
    return moment.replace(hour=minute // 60, minute=minute % 60)


@dataclass(frozen=True)
class PeriodInstance:
    """One period of one ski day, e.g. "evening of 2026-12-14", for one massif.

    ``start``/``end`` are aware local datetimes. For a time slot they are the KPI
    window; for a ``native_window`` period they only say when it is shown.
    """

    period: Period
    day_offset: int
    ski_day: date
    start: datetime
    end: datetime

    @property
    def period_id(self) -> str:
        return self.period.id

    @property
    def key(self) -> str:
        """Stable identifier across runs, e.g. ``evening@2026-12-14``."""
        return f"{self.period.id}@{self.ski_day.isoformat()}"


@dataclass
class RunContext:
    """Everything a layer needs to know about the current run.

    ``run_date`` is the *ski day* running when the run started: the local date,
    or the previous one before ``day_start`` (06:00), so a refresh at 00:00
    still describes the evening and night of the day before. KPIs are computed
    for the periods of ``run_date`` and the next days (``horizon_days``).
    """

    config: Config
    storage: Storage
    run_date: date
    run_id: str
    generated_at: datetime
    massif_ids: list[str] | None = None
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
        run_id: str | None = None,
    ) -> RunContext:
        """Context of a run starting ``now``.

        ``run_id`` pins the run start (and so ``now``): every job of a CI run
        passes the same id so they all agree on dates and visible periods.
        """
        if run_id is not None:
            now = parse_run_id(run_id)
        now = now or datetime.now(UTC)
        if run_date is None:
            first = config.enabled_massifs(massif_ids)
            tz = first[0].tz if first else ZoneInfo("UTC")
            run_date = ski_day(config, now, tz)
        return cls(
            config=config,
            storage=storage,
            run_date=run_date,
            run_id=make_run_id(now),
            generated_at=now.astimezone(UTC).replace(microsecond=0),
            massif_ids=massif_ids,
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

    def period_instances(
        self, massif: Massif, period_ids: list[str] | None = None, *, visible_only: bool = True
    ) -> list[PeriodInstance]:
        """Periods of the horizon for ``massif``, sorted by start then config order.

        ``period_ids`` restricts the periods (e.g. those of a KPI). With
        ``visible_only``, periods already over at ``generated_at`` are dropped.
        """
        periods_file = self.config.periods
        start_time = parse_local_time(periods_file.day_start)
        day_start = start_time.hour * 60 + start_time.minute
        instances: list[PeriodInstance] = []
        for offset in range(periods_file.horizon_days):
            day = self.run_date + timedelta(days=offset)
            for period in periods_file.periods:
                if period_ids is not None and period.id not in period_ids:
                    continue
                start, end = periods_file.span(period)
                instance = PeriodInstance(
                    period=period,
                    day_offset=offset,
                    ski_day=day,
                    start=_wall_clock(day, day_start + start, massif.tz),
                    end=_wall_clock(day, day_start + end, massif.tz),
                )
                if visible_only and instance.end <= self.generated_at:
                    continue
                instances.append(instance)
        order = {p.id: i for i, p in enumerate(periods_file.periods)}
        return sorted(instances, key=lambda i: (i.start, order[i.period_id]))

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
