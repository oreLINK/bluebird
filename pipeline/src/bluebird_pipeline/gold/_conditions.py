"""Physical helpers shared by the live KPIs of comfort, snow and sky.

- :func:`wet_bulb_expr`: wet-bulb temperature (Stull 2011), the snowmaking
  criterion (snow cannons need it at about -2.5 °C or below).
- :func:`wind_chill_expr`: felt temperature in the wind (North American and
  UK wind chill index, 2001), valid at or below 10 °C with some wind.
- :func:`base_temperature_expr`: temperature brought down to another
  elevation with the standard lapse rate, for places the ensemble does not
  sample (the bottom of the resort and its road).
- :func:`sunset_utc`: sunset time (NOAA solar position, standard refraction).
"""

from __future__ import annotations

import math
from datetime import UTC, date, datetime, timedelta

import polars as pl

#: Standard atmosphere: temperature change per metre of altitude (°C).
LAPSE_RATE_C_PER_M = 0.0065


def wet_bulb_expr(temp: str = "temperature_c", rh: str = "relative_humidity_pct") -> pl.Expr:
    """Wet-bulb temperature (°C) from temperature (°C) and relative humidity (%)."""
    t, r = pl.col(temp), pl.col(rh)
    return (
        t * (0.151977 * (r + 8.313659).sqrt()).arctan()
        + (t + r).arctan()
        - (r - 1.676331).arctan()
        + 0.00391838 * r.pow(1.5) * (0.023101 * r).arctan()
        - 4.686035
    )


def wind_chill_expr(temp: str = "temperature_c", wind: str = "wind_speed_kmh") -> pl.Expr:
    """Wind chill (°C); the air temperature itself above 10 °C or below 4.8 km/h."""
    t, v = pl.col(temp), pl.col(wind)
    chill = 13.12 + 0.6215 * t - 11.37 * v.pow(0.16) + 0.3965 * t * v.pow(0.16)
    return pl.when((t <= 10) & (v >= 4.8)).then(pl.min_horizontal(chill, t)).otherwise(t)


def base_temperature_expr(target_m: float, temp: str = "temperature_c") -> pl.Expr:
    """Temperature at ``target_m`` from the row's temperature at ``elevation_m``."""
    return pl.col(temp) + (pl.col("elevation_m") - target_m) * LAPSE_RATE_C_PER_M


def sunset_utc(day: date, lat: float, lon: float) -> datetime:
    """Sunset (UTC, to about a minute) on ``day`` at a place (NOAA equations).

    The sun's upper edge touches the horizon (-0.833° with refraction); the
    terrain is not taken into account, so ridges to the west hide it earlier.
    """
    gamma = 2 * math.pi / 365 * (day.timetuple().tm_yday - 1)
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
    phi = math.radians(lat)
    cos_ha = math.cos(math.radians(90.833)) / (math.cos(phi) * math.cos(decl)) - math.tan(
        phi
    ) * math.tan(decl)
    hour_angle = math.degrees(math.acos(max(-1.0, min(1.0, cos_ha))))
    minutes = 720 - 4 * (lon - hour_angle) - eqtime
    return datetime(day.year, day.month, day.day, tzinfo=UTC) + timedelta(minutes=minutes)
