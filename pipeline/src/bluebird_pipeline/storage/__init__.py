"""Storage abstraction for the medallion layers.

Layers never touch the filesystem directly: they read and write *keys* (POSIX
style relative paths such as ``gold/kpis/date=2026-12-14/kpis.parquet``) through
a :class:`Storage`. Only :class:`LocalStorage` exists today; a cloud backend
can be added later by implementing the four abstract methods.
"""

from .base import Storage
from .keys import (
    bronze_key,
    diamond_key,
    gold_key,
    latest_key,
    rewind_gold_key,
    rewind_key,
    silver_key,
)
from .local import LocalStorage

__all__ = [
    "LocalStorage",
    "Storage",
    "bronze_key",
    "diamond_key",
    "gold_key",
    "latest_key",
    "rewind_gold_key",
    "rewind_key",
    "silver_key",
]
