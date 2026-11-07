"""Silver dataset ``avalanche_bulletin``: the Météo-France avalanche bulletins (BRA).

One row per avalanche massif, bulletin and day. Météo-France publishes a
bulletin per massif every afternoon (about 16:00 local) for the next day,
from early November to late May, and may amend it. The danger level follows
the European scale, 1 (low) to 5 (very high).

Each bulletin gives two rows:

- the bulletin itself (``trend`` false), for the day it is valid for. When it
  splits the level by elevation, ``level_low`` applies below
  ``altitude_limit_m`` and ``level_high`` above it; otherwise both hold the
  same level and the limit is null. A level that changes during the day
  (``EVOLURISQUE``) and a geographic split (east/west, north/south of the
  massif: we do not know the side of each resort) both keep the higher level;
- its trend for the day after (``trend`` true, ``RISQUEMAXIJ2``): only the
  maximum level, without elevation split. It lets the morning refreshes show
  tomorrow before the afternoon bulletin, which replaces it.

The parser is :mod:`.transformer_meteofrance_bra`; the ``avalanche_risk``
aggregator and the demo data share this contract.
"""

from __future__ import annotations

from typing import Any

import polars as pl

AVALANCHE_DATASET = "avalanche_bulletin"

AVALANCHE_SCHEMA: dict[str, Any] = {
    "massif_number": pl.Int32,  # Météo-France massif number (stations: `avalanche_massif`)
    "massif_name": pl.Utf8,
    "valid_date": pl.Date,  # local day the row is valid for
    "level_low": pl.Int8,  # 1..5, below `altitude_limit_m` (or everywhere)
    "level_high": pl.Int8,  # 1..5, above `altitude_limit_m` (or everywhere)
    "altitude_limit_m": pl.Int32,  # null when the level does not depend on elevation
    "trend": pl.Boolean,  # true: the day-after trend of an earlier bulletin (max level only)
    "issued_at": pl.Datetime("us", "UTC"),
}
