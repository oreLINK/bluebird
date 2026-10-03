"""Helpers to reduce hourly ensemble tables to one value per member.

Open-Meteo hourly values are valid for the hour *ending* at their timestamp
(accumulations such as snowfall are the sum over the preceding hour). A window
``(start, end]`` therefore selects timestamps strictly after ``start`` and up
to and including ``end``.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

import polars as pl

Reduction = Literal["sum", "max", "min", "mean"]


def member_window(
    frame: pl.DataFrame,
    *,
    station_id: str,
    band: str,
    start: datetime,
    end: datetime,
    column: str,
    how: Reduction,
    alias: str = "value",
) -> pl.DataFrame:
    """Reduce ``column`` over ``(start, end]`` for each ``(model, member)``.

    Members missing any hour of the window, or with null values, are dropped,
    so a partial download never biases a probability. Returns columns
    ``model``, ``member`` and ``alias``.
    """
    start_utc, end_utc = start.astimezone(UTC), end.astimezone(UTC)
    expected_hours = round((end_utc - start_utc).total_seconds() / 3600)
    reducer = getattr(pl.col(column), how)()
    return (
        frame.filter(
            (pl.col("station_id") == station_id)
            & (pl.col("band") == band)
            & (pl.col("time_utc") > start_utc)
            & (pl.col("time_utc") <= end_utc)
        )
        .group_by("model", "member")
        .agg(reducer.alias(alias), pl.col(column).count().alias("_valid_hours"))
        .filter(pl.col("_valid_hours") >= expected_hours)
        .drop("_valid_hours")
        .sort("model", "member")
    )


def quantile(values: pl.Series, q: float, decimals: int = 1) -> float | None:
    """Rounded quantile of ``values`` (``None`` for an empty series)."""
    if values.is_empty():
        return None
    result = values.quantile(q, interpolation="linear")
    return None if result is None else round(float(result), decimals)
