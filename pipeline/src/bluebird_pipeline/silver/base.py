"""Silver layer contract: ``Transformer`` classes turn one bronze batch into a table.

Silver tables are typed, tidy (one row per observation) and use canonical
column names and units, whatever the source:

- times in UTC (``time_utc``), heights in metres, temperatures in °C,
  precipitation in mm, snowfall in cm, wind in km/h.

Each Transformer declares the ``dataset`` it produces and its column ``schema``;
:meth:`Transformer.conform` enforces it so gold code can rely on it.

Reference datasets (sources with ``schedule: reference``, e.g. pistes and lifts)
are also serialised to committed files under ``config/reference/``: such a
Transformer sets ``reference_suffix`` and implements :meth:`reference_file`
and :meth:`read_reference`. See :mod:`bluebird_pipeline.reference`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar

import polars as pl

from ..bronze.base import BronzeBatch
from ..config import Massif, Source
from ..context import RunContext
from ..registry import Registry


class Transformer(ABC):
    """Clean and normalise the bronze batch of one source.

    Subclasses set ``dataset`` and ``schema``, implement :meth:`transform`, and
    register with ``@register_transformer("id")``.
    """

    id: ClassVar[str]
    dataset: ClassVar[str]
    schema: ClassVar[dict[str, Any]]

    #: Extension of the committed reference file (e.g. ".geojson") when this
    #: dataset is reference data; ``None`` for daily data.
    reference_suffix: ClassVar[str | None] = None

    def __init__(self, source: Source) -> None:
        self.source = source

    @abstractmethod
    def transform(self, batch: BronzeBatch, ctx: RunContext) -> pl.DataFrame:
        """Return the silver table for ``batch``; call :meth:`conform` before returning."""

    def reference_file(self, frame: pl.DataFrame, massif: Massif, ctx: RunContext) -> bytes | None:
        """Serialise the rows of ``massif`` as a reference file, or ``None`` if it has no rows.

        The output must be deterministic (sorted, stable formatting) so that a
        refresh produces a readable diff in the pull request.
        """
        raise NotImplementedError(f"{type(self).__name__} does not produce reference data")

    @classmethod
    def read_reference(cls, content: bytes) -> pl.DataFrame:
        """Parse one reference file back into a table with :attr:`schema`."""
        raise NotImplementedError(f"{cls.__name__} does not produce reference data")

    def conform(self, frame: pl.DataFrame) -> pl.DataFrame:
        """Add missing columns as nulls, cast every column, and order them as ``schema``."""
        missing = [name for name in self.schema if name not in frame.columns]
        if missing:
            frame = frame.with_columns(pl.lit(None).alias(name) for name in missing)
        return frame.select(pl.col(name).cast(dtype) for name, dtype in self.schema.items())


TRANSFORMERS: Registry[Transformer] = Registry("transformer")
register_transformer = TRANSFORMERS.register
