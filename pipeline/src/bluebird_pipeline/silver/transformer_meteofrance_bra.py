"""Météo-France avalanche bulletins (BRA XML) → silver ``avalanche_bulletin``.

The dataset contract (columns, meaning) lives in :mod:`._avalanche`. Fields
read, after the "Descriptif technique des informations du bulletin
avalanche" of Météo-France:

- root ``BULLETINS_NEIGE_AVALANCHE``: ``ID`` (massif number), ``MASSIF``,
  ``DATEBULLETIN`` (written, in UTC: "J vers 16h" local), ``DATEVALIDITE``
  (in UTC, the day after at 18:00 in general);
- ``CARTOUCHERISQUE/RISQUE``: ``RISQUE1`` (always set, the lower band when
  split), ``RISQUE2`` (empty, or the upper band / the other side), ``LOC1``
  ("<2100", "E" or "S"), ``LOC2`` (">2100", "O" or "N"), ``ALTITUDE`` (the
  limit of an elevation split), ``EVOLURISQUE1/2`` (the level later in the
  day), ``RISQUEMAXI``, ``RISQUEMAXIJ2`` and ``DATE_RISQUE_J2`` (the trend of
  the day after).

Records without payload (no bulletin for the massif) are skipped: out of
season the table is empty, which is not an error.
"""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from datetime import UTC, date, datetime
from typing import Any, ClassVar
from zoneinfo import ZoneInfo

import polars as pl

from ..bronze.base import BronzeBatch
from ..context import RunContext
from ._avalanche import AVALANCHE_DATASET, AVALANCHE_SCHEMA
from .base import Transformer, register_transformer

log = logging.getLogger(__name__)

PARIS = ZoneInfo("Europe/Paris")


def _level(value: str | None) -> int | None:
    """A danger level 1..5 from an XML attribute, ``None`` when empty or invalid."""
    text = (value or "").strip()
    if not text.isdigit():
        return None
    level = int(text)
    return level if 1 <= level <= 5 else None


def _number(value: str | None) -> int | None:
    text = (value or "").strip()
    return int(text) if text.isdigit() else None


def _utc(value: str | None) -> datetime | None:
    """A BRA date (naive ISO, in UTC) as an aware datetime."""
    text = (value or "").strip()
    if not text:
        return None
    return datetime.fromisoformat(text).replace(tzinfo=UTC)


def _band(level: int | None, later: int | None) -> int | None:
    """Level of one band over the day: the higher of the level and its evolution."""
    values = [v for v in (level, later) if v is not None]
    return max(values) if values else None


def parse_bulletin(xml: str, tz: ZoneInfo = PARIS) -> list[dict[str, Any]]:
    """Rows of one BRA XML bulletin: the bulletin, then its day-after trend.

    ``tz`` is the massif's timezone, to turn the UTC validity time into the
    local day the bulletin covers.
    """
    root = ET.fromstring(xml.encode("utf-8"))
    risk = root.find("CARTOUCHERISQUE/RISQUE")
    number = _number(root.get("ID"))
    issued = _utc(root.get("DATEBULLETIN"))
    valid = _utc(root.get("DATEVALIDITE")) or _utc(root.findtext("DateValidite"))
    if risk is None or number is None or issued is None or valid is None:
        return []

    first = _band(_level(risk.get("RISQUE1")), _level(risk.get("EVOLURISQUE1")))
    if first is None:
        return []
    second = _band(_level(risk.get("RISQUE2")), _level(risk.get("EVOLURISQUE2")))
    limit = _number(risk.get("ALTITUDE"))
    if second is None:
        low = high = first
        limit = None
    elif limit is not None:
        # RISQUE1 is the lower band ("<2100"); swap if LOC1 ever says otherwise.
        low, high = first, second
        if (risk.get("LOC1") or "").strip().startswith(">"):
            low, high = high, low
    else:
        # Geographic split (east/west, south/north): the side of a resort is
        # unknown, so keep the higher level.
        low = high = max(first, second, _level(risk.get("RISQUEMAXI")) or 0)

    base = {"massif_number": number, "massif_name": root.get("MASSIF"), "issued_at": issued}
    rows = [
        {
            **base,
            "valid_date": valid.astimezone(tz).date(),
            "level_low": low,
            "level_high": high,
            "altitude_limit_m": limit,
            "trend": False,
        }
    ]
    trend = _level(risk.get("RISQUEMAXIJ2"))
    trend_day = (risk.get("DATE_RISQUE_J2") or "").strip()
    if trend is not None and trend_day:
        rows.append(
            {
                **base,
                "valid_date": date.fromisoformat(trend_day[:10]),
                "level_low": trend,
                "level_high": trend,
                "altitude_limit_m": None,
                "trend": True,
            }
        )
    return rows


@register_transformer("meteofrance_bra")
class TransformerMeteofranceBra(Transformer):
    """One row per massif, bulletin and day (the bulletin and its day-after trend)."""

    dataset: ClassVar[str] = AVALANCHE_DATASET
    schema: ClassVar[dict[str, Any]] = AVALANCHE_SCHEMA

    def transform(self, batch: BronzeBatch, ctx: RunContext) -> pl.DataFrame:
        zones = {
            ref.station.avalanche_massif: ref.massif.tz
            for ref in ctx.stations()
            if ref.station.avalanche_massif is not None
        }
        rows: list[dict[str, Any]] = []
        for record in batch.records:
            if not record.payload:
                continue
            number = record.context.get("massif_number")
            try:
                rows.extend(parse_bulletin(record.payload, zones.get(number, PARIS)))
            except ET.ParseError as exc:
                log.warning("%s: massif %s: invalid XML (%s)", self.id, number, exc)
        frame = (
            pl.DataFrame(rows, schema=AVALANCHE_SCHEMA)
            if rows
            else pl.DataFrame(schema=AVALANCHE_SCHEMA)
        )
        return self.conform(frame)
