"""White days ("jours blancs"): shared by the live and the historical KPIs.

A white day is a ski day without relief: skiing inside the cloud or under a
thick overcast sky, often in snow. No variable of the models measures it (the
AROME archive has no visibility, and never reports fog), so an hour is
*white* when at least one of these holds, from hourly model values:

1. **in the cloud**: relative humidity >= ``rh_min_pct`` and low cloud cover
   >= ``low_cloud_min_pct`` (total cloud cover when the model has no low cloud
   cover, e.g. the ICON ensemble);
2. **steady snowfall**: snowfall >= ``snowfall_min_cm_h``;
3. **flat light**: global radiation below ``clear_sky_index_max`` times the
   clear-sky radiation of that hour (sun position, Haurwitz model), when the
   sun is high enough for it to mean anything.

A day is white when at least ``min_white_hours`` of its ski hours
(``ski_start``..``ski_end``, local) are white. Values describe the hour ending
at their timestamp, so the sun position is taken half an hour earlier.
"""

from __future__ import annotations

import math
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import polars as pl
from pydantic import Field, model_validator

from ..config import LocalTime, parse_local_time
from .base import AggregatorParams

_HALF_HOUR = timedelta(minutes=30)
#: Below this clear-sky radiation (W/m²) the sun is too low for the flat-light test.
_MIN_CLEAR_SKY_WM2 = 50.0


class WhiteoutRule(AggregatorParams):
    """Thresholds of a white hour and a white day (KPI `params`)."""

    rh_min_pct: float = Field(default=98.0, gt=0, le=100)
    low_cloud_min_pct: float = Field(default=90.0, gt=0, le=100)
    snowfall_min_cm_h: float = Field(default=0.5, gt=0)
    clear_sky_index_max: float = Field(default=0.3, gt=0, lt=1)
    ski_start: LocalTime = "09:00"
    ski_end: LocalTime = "17:00"
    min_white_hours: int = Field(default=6, ge=1, le=24)

    @model_validator(mode="after")
    def _window(self) -> WhiteoutRule:
        if parse_local_time(self.ski_end) <= parse_local_time(self.ski_start):
            raise ValueError("ski_end must be after ski_start")
        if self.min_white_hours > self.ski_hours:
            raise ValueError("min_white_hours exceeds the ski hours")
        return self

    @property
    def ski_hours(self) -> int:
        start, end = parse_local_time(self.ski_start), parse_local_time(self.ski_end)
        return round((_minutes(end) - _minutes(start)) / 60)

    def ski_window(self, day: date, tz: ZoneInfo) -> tuple[datetime, datetime]:
        """``(start, end]`` of the ski hours of local ``day`` in ``tz``."""
        start = datetime.combine(day, parse_local_time(self.ski_start), tzinfo=tz)
        end = datetime.combine(day, parse_local_time(self.ski_end), tzinfo=tz)
        return start, end


def clear_sky_ghi(when: datetime, lat: float, lon: float) -> float:
    """Clear-sky global horizontal irradiance (W/m²) at ``when`` (aware) and a place.

    NOAA solar position (accurate to a few minutes) and the Haurwitz clear-sky
    model; plain Python twin of :func:`clear_sky_expr`, used in tests.
    """
    utc = when.astimezone(UTC)
    doy = utc.timetuple().tm_yday
    hour = utc.hour + utc.minute / 60 + utc.second / 3600
    gamma = 2 * math.pi / 365 * (doy - 1 + (hour - 12) / 24)
    eqtime = 229.18 * (
        0.000075
        + 0.001868 * math.cos(gamma)
        - 0.032077 * math.sin(gamma)
        - 0.014615 * math.cos(2 * gamma)
        - 0.040849 * math.sin(2 * gamma)
    )
    decl = (
        0.006918
        - 0.399912 * math.cos(gamma)
        + 0.070257 * math.sin(gamma)
        - 0.006758 * math.cos(2 * gamma)
        + 0.000907 * math.sin(2 * gamma)
        - 0.002697 * math.cos(3 * gamma)
        + 0.00148 * math.sin(3 * gamma)
    )
    true_solar_minutes = hour * 60 + eqtime + 4 * lon
    hour_angle = math.radians(true_solar_minutes / 4 - 180)
    phi = math.radians(lat)
    cos_zenith = math.sin(phi) * math.sin(decl) + math.cos(phi) * math.cos(decl) * math.cos(
        hour_angle
    )
    if cos_zenith <= 0:
        return 0.0
    return 1098.0 * cos_zenith * math.exp(-0.057 / cos_zenith)


def clear_sky_expr(time_col: str, lat: pl.Expr | float, lon: pl.Expr | float) -> pl.Expr:
    """Polars twin of :func:`clear_sky_ghi`, for the hour ending at ``time_col``."""
    lat_e = lat if isinstance(lat, pl.Expr) else pl.lit(lat)
    lon_e = lon if isinstance(lon, pl.Expr) else pl.lit(lon)
    t = (pl.col(time_col) - pl.duration(minutes=30)).dt.convert_time_zone("UTC")
    hour = t.dt.hour() + t.dt.minute() / 60
    gamma = 2 * math.pi / 365 * (t.dt.ordinal_day() - 1 + (hour - 12) / 24)
    eqtime = 229.18 * (
        0.000075
        + 0.001868 * gamma.cos()
        - 0.032077 * gamma.sin()
        - 0.014615 * (2 * gamma).cos()
        - 0.040849 * (2 * gamma).sin()
    )
    decl = (
        0.006918
        - 0.399912 * gamma.cos()
        + 0.070257 * gamma.sin()
        - 0.006758 * (2 * gamma).cos()
        + 0.000907 * (2 * gamma).sin()
        - 0.002697 * (3 * gamma).cos()
        + 0.00148 * (3 * gamma).sin()
    )
    hour_angle = ((hour * 60 + eqtime + 4 * lon_e) / 4 - 180) * (math.pi / 180)
    phi = lat_e * (math.pi / 180)
    cos_z = phi.sin() * decl.sin() + phi.cos() * decl.cos() * hour_angle.cos()
    return pl.when(cos_z > 0).then(1098.0 * cos_z * (-0.057 / cos_z).exp()).otherwise(0.0)


def white_hour_expr(rule: WhiteoutRule, clear_sky: pl.Expr) -> pl.Expr:
    """True when the hour is white (see the module docstring). Needs the silver columns."""
    low_cloud = pl.coalesce("cloud_cover_low_pct", "cloud_cover_pct")
    in_cloud = (pl.col("relative_humidity_pct") >= rule.rh_min_pct) & (
        low_cloud >= rule.low_cloud_min_pct
    )
    snowing = pl.col("snowfall_cm") >= rule.snowfall_min_cm_h
    flat_light = (clear_sky >= _MIN_CLEAR_SKY_WM2) & (
        pl.col("shortwave_wm2") < rule.clear_sky_index_max * clear_sky
    )
    return in_cloud.fill_null(False) | snowing.fill_null(False) | flat_light.fill_null(False)


def ski_hours_mask(rule: WhiteoutRule, tz_name: str) -> pl.Expr:
    """True for rows whose hour ends within the ski hours ``(ski_start, ski_end]`` (local)."""
    local = pl.col("time_utc").dt.convert_time_zone(tz_name)
    minutes = local.dt.hour().cast(pl.Int32) * 60 + local.dt.minute().cast(pl.Int32)
    start = _minutes(parse_local_time(rule.ski_start))
    end = _minutes(parse_local_time(rule.ski_end))
    return (minutes > start) & (minutes <= end)


def local_day_expr(tz_name: str) -> pl.Expr:
    """Local date of the hour ending at ``time_utc``."""
    return (pl.col("time_utc") - pl.duration(minutes=30)).dt.convert_time_zone(tz_name).dt.date()


def _minutes(t: time) -> int:
    return t.hour * 60 + t.minute
