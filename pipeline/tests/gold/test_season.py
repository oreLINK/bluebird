"""Maths of the historical (Rewind) KPIs."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from bluebird_pipeline.gold._season import longest_episode

T0 = datetime(2026, 1, 10, tzinfo=UTC)


def _hours(values: list[float]) -> tuple[list[datetime], list[float]]:
    return [T0 + timedelta(hours=i) for i in range(len(values))], values


def test_longest_episode_bridges_short_lulls_only() -> None:
    #           0    1    2    3    4    5    6    7    8    9
    times, snow = _hours([0.5, 0.5, 0.0, 0.4, 0.0, 0.0, 0.3, 0.3, 0.3, 0.0])
    episode = longest_episode(times, snow, min_rate_cm_h=0.1, max_gap_hours=1)
    assert episode is not None
    # Hours 0-3 (one dry hour bridged) = 4 h; hours 6-8 = 3 h after a 2 h lull.
    assert (episode.hours, episode.snow_cm) == (4, 1.4)
    assert episode.start == T0 - timedelta(hours=1)
    assert episode.end == T0 + timedelta(hours=3)


def test_longest_episode_without_gaps_and_ties() -> None:
    times, snow = _hours([0.2, 0.0, 0.5, 0.0, 0.2])
    episode = longest_episode(times, snow, min_rate_cm_h=0.1, max_gap_hours=0)
    assert episode is not None
    assert (episode.hours, episode.snow_cm) == (1, 0.5)  # tie on hours: more snow wins


def test_missing_hours_count_as_dry() -> None:
    times = [T0, T0 + timedelta(hours=1), T0 + timedelta(hours=5)]
    episode = longest_episode(times, [0.3, 0.3, 0.3], min_rate_cm_h=0.1, max_gap_hours=2)
    assert episode is not None and episode.hours == 2


def test_no_snow_gives_no_episode() -> None:
    times, snow = _hours([0.0, 0.05, 0.0])
    assert longest_episode(times, snow, min_rate_cm_h=0.1, max_gap_hours=1) is None
