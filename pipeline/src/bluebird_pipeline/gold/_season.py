"""Helpers shared by the historical (Rewind) aggregators.

They work on ``season_hourly`` rows already limited to the season window
``(start, end]``. Open-Meteo values describe the hour *ending* at their
timestamp, so the hour starting at ``t - 1 h`` is the one reported at ``t``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import polars as pl

from ..config import Rewind

HOUR = timedelta(hours=1)


def season_hours(rewind: Rewind, tz: ZoneInfo) -> int:
    """Number of hours in the season window."""
    start, end = rewind.window(tz)
    return round((end - start) / HOUR)


def in_window(hourly: pl.DataFrame, rewind: Rewind, tz: ZoneInfo) -> pl.DataFrame:
    """Rows whose hour ends in ``(start, end]`` of the season."""
    start, end = (t.astimezone(UTC) for t in rewind.window(tz))
    return hourly.filter((pl.col("time_utc") > start) & (pl.col("time_utc") <= end))


def point_totals(hourly: pl.DataFrame, kind: str, min_hours: int) -> pl.DataFrame:
    """Season snowfall per station and point of ``kind``, for points with enough hours.

    Columns: ``station_id``, ``point_id``, ``snowfall_cm``, ``hours``.
    """
    return (
        hourly.filter((pl.col("point_kind") == kind) & pl.col("snowfall_cm").is_not_null())
        .group_by("station_id", "point_id")
        .agg(pl.col("snowfall_cm").cast(pl.Float64).sum(), hours=pl.len())
        .filter(pl.col("hours") >= min_hours)
        .sort("station_id", "point_id")
    )


def local_days(times: list[datetime], tz: ZoneInfo) -> list[str]:
    """Local date (ISO) of the hour ending at each timestamp."""
    return [(t - HOUR).astimezone(tz).date().isoformat() for t in times]


@dataclass(frozen=True)
class Episode:
    """A continuous snowfall: from the start of its first snowy hour to the end of its last."""

    start: datetime
    end: datetime
    hours: int
    snow_cm: float


def longest_episode(
    times: list[datetime], snow: list[float], *, min_rate_cm_h: float, max_gap_hours: int
) -> Episode | None:
    """Longest run of snowy hours (``snow >= min_rate_cm_h``) in time order.

    Up to ``max_gap_hours`` dry or missing hours inside an episode do not break
    it. Ties go to the episode with more snow, then to the earliest one.
    """
    best: Episode | None = None
    first: datetime | None = None
    last: datetime | None = None
    total = 0.0
    pending = 0.0  # snow of dry hours since the last snowy hour

    def close() -> None:
        nonlocal best
        if first is None or last is None:
            return
        episode = Episode(
            start=first - HOUR,
            end=last,
            hours=round((last - first) / HOUR) + 1,
            snow_cm=round(total, 1),
        )
        if best is None or (episode.hours, episode.snow_cm) > (best.hours, best.snow_cm):
            best = episode

    for t, value in sorted(zip(times, snow, strict=True)):
        amount = value or 0.0
        if amount >= min_rate_cm_h:
            if last is not None and (t - last) <= HOUR * (max_gap_hours + 1):
                total += pending + amount
            else:
                close()
                first, total = t, amount
            last, pending = t, 0.0
        elif last is not None:
            pending += amount
    close()
    return best
